import re
from rouge_metric import PyRouge
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
# from readability import Readability
# from readability.scorers import FleschKincaid
import textstat
from bleurt import score


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
        bleu_score = sentence_bleu([can], ref, smoothing_function=SmoothingFunction().method0)
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
    def calculateBleurtScore(reference, candidate, checkpoint="BLEURT-20") -> list:
        scorer = score.LengthBatchingBleurtScorer(checkpoint)
        bleurt_scores = scorer.score(references=reference, candidates=candidate)
        assert isinstance(bleurt_scores, list) and len(bleurt_scores) == 1
        return bleurt_scores
