import re
from rouge_metric import PyRouge
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
# from readability import Readability
# from readability.scorers import FleschKincaid
import textstat
from sklearn.feature_extraction.text import TfidfVectorizer
from bleurt import score
import requests
import json
import pandas as pd
import datetime
import os


class MetricHelper:

    @staticmethod
    def calculate_rouge_score(reference, candidate) -> dict:
        reference = [reference]
        candidate = [candidate]

        rouge = PyRouge(rouge_n=(1, 2, 4), rouge_l=True, skip_gap=4)
        rouge_scores = rouge.evaluate(candidate, reference)
        return rouge_scores

    @staticmethod
    def calculateBleuScore(reference, candidate) -> float:
        ref = re.sub('\W+', ' ', reference).split(' ')
        can = re.sub('\W+', ' ', candidate).split(' ')
        bleu_score = sentence_bleu([can], ref, smoothing_function=SmoothingFunction().method1)
        return bleu_score

    # @staticmethod
    # def calculateFKReadability(candidate) -> float:
    #     r = Readability(candidate, min_words=1)
    #     # fk = r.flesch_kincaid()
    #     r._statistics.num_words = 1
    #     fk = FleschKincaid(r._statistics, min_words=1)
    #     fk_score = fk.score
    #     return fk_score

    @staticmethod
    def calculateFKScore(candidate) -> float:
        return textstat.flesch_kincaid_grade(candidate)

    @staticmethod
    def calculateReadability(text) -> float:
        return textstat.flesch_reading_ease(text)

    @staticmethod
    def calculateBleurtScore(reference, candidate, checkpoint="BLEURT-20") -> list:
        scorer = score.LengthBatchingBleurtScorer(checkpoint)
        bleurt_scores = scorer.score(references=reference, candidates=candidate)
        assert isinstance(bleurt_scores, list)
        return bleurt_scores

    @staticmethod
    def calculateCosineSimilarity(documents):
        vect = TfidfVectorizer(min_df=1, stop_words='english')
        tfidf = vect.fit_transform(documents)
        pairwise_similarity = tfidf * tfidf.T
        return pairwise_similarity.toarray()


class InferenceHelper:

    
    @staticmethod
    def runInference(prompt, model='deepseek-llm:7b'):
        url = "http://localhost:11434/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        schema = {
            "$schema": "seml-schema",
            "title": "Explanation",
            "description": "A failure explanation",
            "type": "object",
            "properties": {
                "explanation": {
                    "description": "The generated explanation",
                    "type": "string"
                }
            },
            "required": ["explanation"]
        }
        data_json = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": schema
        }

        response = requests.post(url, headers=headers, data=json.dumps(data_json))
        try:
            r = json.loads(response.text)['response']
            return r
        except:
            print(response.text)
            return response.text
    
    @staticmethod
    def generatePrompt(explanations, method, mode, df, ref_df):
        prompt_input = PromptHelper.prompt_input_default
        prompt_output = PromptHelper.prompt_output_default
        if mode == 'default':
            prompt_task = PromptHelper.prompt_task_professional
        if mode == 'source':
            prompt_task = PromptHelper.prompt_task_source + PromptHelper.prompt_context_source + PromptHelper.load_source_files()[method]
        if mode == 'error':
            test, error = PromptHelper.get_test_error(method, ref_df)
            prompt_task = PromptHelper.prompt_task_test + PromptHelper.prompt_context_test + test + error
        if mode == 'oneshot':
            expl, c, d = PromptHelper.get_examples(method, df, ref_df)
            prompt_task = PromptHelper.prompt_task_professional + PromptHelper.prompt_task_oneshot_in + expl + PromptHelper.prompt_task_oneshot_out_one + c + PromptHelper.prompt_task_oneshot_out_two + d
        input = '\n\n' + '\n\n'.join(["'''\n" + expl + "\n'''" for expl in explanations]) + '\n\n'
        prompt = prompt_task + prompt_input + input + prompt_output
        return prompt
    
    @staticmethod
    def generateExplanationsWithMetrics(df, ref_df, model='deepseek-llm:7b', mode='default'):
        generated_explanations = {}
        methods = df['File'].unique().tolist()
        for method in methods:
            method_explanations = df[(df['File'] == method)]['Explanation'].to_list()
            prompt = InferenceHelper.generatePrompt(method_explanations, method, mode, df, ref_df)
            inference = InferenceHelper.runInference(prompt, model)
            try:
                generated_explanations[method] = json.loads(inference)['explanation']
            except:
                generated_explanations[method] = inference

        generated_explanations_df = pd.DataFrame.from_dict(generated_explanations, orient='index', columns=['explanation'])
        generated_explanations_df = generated_explanations_df.join(ref_df.set_index('bug')['description_c']).join(ref_df.set_index('bug')['description_d'])

        metric_df = InferenceHelper.calculate_metrics(generated_explanations_df)
        metric_df.to_csv('output/' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") +'_' + mode + '.csv')
        return metric_df



    @staticmethod
    def calculate_metrics(df):
        explanations = df['explanation'].to_list()
        explanations_c = df['description_c'].to_list()
        explanations_d = df['description_d'].to_list()

        df['bleu_c'] = df.apply(lambda row: MetricHelper.calculateBleuScore(row.description_c, row.explanation), axis=1)
        df['bleu_d'] = df.apply(lambda row: MetricHelper.calculateBleuScore(row.description_d, row.explanation), axis=1)
        df['readablity'] = df.apply(lambda row: MetricHelper.calculateReadability(row.explanation), axis=1)
        df['readablity_c'] = df.apply(lambda row: MetricHelper.calculateReadability(row.description_c), axis=1)
        df['readablity_d'] = df.apply(lambda row: MetricHelper.calculateReadability(row.description_d), axis=1)
        df['cosine_c'] = df.apply(lambda row: MetricHelper.calculateCosineSimilarity([row.explanation, row.description_c]), axis=1)
        df['cosine_d'] = df.apply(lambda row: MetricHelper.calculateCosineSimilarity([row.explanation, row.description_d]), axis=1)
        df['rouge_c'] = df.apply(lambda row: MetricHelper.calculate_rouge_score(row.description_c, row.explanation), axis=1)
        df['rouge_d'] = df.apply(lambda row: MetricHelper.calculate_rouge_score(row.description_d, row.explanation), axis=1)
        df['bleurt_c'] = MetricHelper.calculateBleurtScore(explanations_c, explanations)
        df['bleurt_d'] = MetricHelper.calculateBleurtScore(explanations_d, explanations)
        return df


class PromptHelper:
    prompt_input_default = "### Input:\n\nHere are the failure explanations:\n\n"

    prompt_output_default = "### Output:\nFormat your response in valid JSON format with a single field 'explanation' of type string containing your generated explanation."

    prompt_task_professional = "###Task:\nYou are a professional software developer. You are given a number of explanations describing the root cause of a software failure. Based on the given explanations, write a single explanation that contains all the information required to understand the root cause of the bug. The explanation should be succinct and without redundant information"

    prompt_task_source = "###Task:\nYou are a professional software developer. You are given a number of explanations describing the root cause of a software failure. As additional context you are given the source code of the file where the error occurs. Based on the given explanations and the source code, write a single explanation that contains all the information required to understand the root cause of the bug. The explanation should be succinct and without redundant information"

    prompt_context_source = "\n\n###Context:\nHere is the source code for context:\n\n"

    prompt_task_test = "###Task:\nYou are a professional software developer. You are given a number of explanations describing the root cause of a software failure that occured when running a unit test. As additional context you are given the unit test and the resulting error message. Based on the given explanations, the test and error, write a single explanation that contains all the information required to understand the root cause of the test error. The explanation should be succinct and without redundant information"

    prompt_context_test = "\n\n###Context:\nHere is the unit test, followed by the error message:\n\n"

    prompt_task_oneshot_in = "\n\n###Example:\nHere is an example of input explanations and two possible output explanations\n\nInput:\n\n"

    prompt_task_oneshot_out_one = "Output Example 1:\n\n"
    
    prompt_task_oneshot_out_two = "Output Example 2:\n\n"

    @staticmethod
    def load_source_files():
        src_files = {}
        for file in os.listdir('source_files'):
            with open('source_files/' + file, 'r') as f:
                method = file.replace('.java', '')
                src_files[method] = "```java\n" + f.read() + "```\n\n"
        return src_files

    def get_test_error(method, df):
        test = '```\n' + df[(df['bug'] == method)]['test_description'].to_string() + '```\n\n'
        error = '```\n' + df[(df['bug'] == method)]['failure_description'].to_string() + '```\n\n'
        return test, error

    def get_examples(method, df, ref_df):
        if method == 'HIT01_8':
            method = 'HIT02_24'
        expl = '\n\n' + '\n\n'.join(["'''\n" + expl + "\n'''" for expl in df[(df['File'] == method)]['Explanation'].to_list()]) + '\n\n'
        c = '```\n' + ref_df[(ref_df['bug'] == method)]['description_c'].to_string() + '```\n\n'
        d = '```\n' + ref_df[(ref_df['bug'] == method)]['description_d'].to_string() + '```\n\n'
        return expl, c, d