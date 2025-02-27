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


class MetricHelper:

    @staticmethod
    def calculateRougeScore(reference, candidate) -> dict:
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
        return json.loads(response.text)['response']
    
    @staticmethod
    def generatePrompt(explanations, prompt_task, prompt_input='', prompt_output=''):
        input = '\n\n' + '\n\n'.join(["'''\n" + expl + "\n'''" for expl in explanations]) + '\n\n'
        prompt = prompt_task + prompt_input + input + prompt_output
        return prompt
    
    @staticmethod
    def generateExplanationsWithMetrics(methods, df, ref_df, prompt_task, prompt_input='', prompt_output='', model='deepseek-llm:7b'):
        generated_explanations = {}
        for method in methods:
            method_explanations = df[(df['File'] == method)]['Explanation'].to_list()
            prompt = InferenceHelper.generatePrompt(method_explanations, prompt_task, prompt_input, prompt_output)
            generated_explanations[method] = json.loads(InferenceHelper.runInference(prompt, model))['explanation']

        generated_explanations_df = pd.DataFrame.from_dict(generated_explanations, orient='index', columns=['explanation'])
        generated_explanations_df = generated_explanations_df.join(ref_df.set_index('bug')['description_c']).join(ref_df.set_index('bug')['description_d'])

        metric_df = InferenceHelper.calculate_metrics(generated_explanations_df)
        metric_df.to_csv('output/' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.csv')
        return metric_df, generated_explanations_df



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
        df['rouge_c'] = df.apply(lambda row: MetricHelper.calculateRougeScore(row.description_c, row.explanation), axis=1)
        df['rouge_d'] = df.apply(lambda row: MetricHelper.calculateRougeScore(row.description_d, row.explanation), axis=1)
        df['bleurt_c'] = MetricHelper.calculateBleurtScore(explanations_c, explanations)
        df['bleurt_d'] = MetricHelper.calculateBleurtScore(explanations_d, explanations)
        return df