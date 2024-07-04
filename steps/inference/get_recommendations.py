from typing import Any, Tuple, Dict, List
import pandas as pd
from collections import defaultdict
from surprise import accuracy
from zenml import step


def precision_recall_at_k(predictions: List[Tuple], k: int = 10, threshold: float = 3.5) -> Tuple[float, float]:
    user_est_true = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))

    precisions = dict()
    recalls = dict()

    for uid, user_ratings in user_est_true.items():
        user_ratings.sort(key=lambda x: x[0], reverse=True)
        n_rel = sum((true_r >= threshold) for (_, true_r) in user_ratings)
        n_rec_k = min(k, len(user_ratings))  # Adjust n_rec_k to be the minimum of k and the number of user ratings
        n_rel_and_rec_k = sum(((true_r >= threshold) and (est >= threshold)) for (est, true_r) in user_ratings[:n_rec_k])
        
        precisions[uid] = n_rel_and_rec_k / n_rec_k if n_rec_k != 0 else 1
        recalls[uid] = n_rel_and_rec_k / n_rel if n_rel != 0 else 1

    precision = sum(prec for prec in precisions.values()) / len(precisions)
    recall = sum(rec for rec in recalls.values()) / len(recalls)
    return precision, recall

def get_model_recommendations(model: Any, test_data: List[Tuple]) -> List[Tuple]:
    predictions = model.test(test_data)
    return predictions

@step
def make_predictions(
    svd_model: Any, knn_model: Any, baseline_model: Any, content_model: Dict[str, Any], raw_test_data: pd.DataFrame, k: int = 10
) -> Dict[str, Any]:
    test_data_tuples = [(d['userId'], d['id'], d['rating']) for d in raw_test_data.to_dict(orient='records')]

    svd_recommendations = get_model_recommendations(svd_model, test_data_tuples)
    knn_recommendations = get_model_recommendations(knn_model, test_data_tuples)
    baseline_recommendations = get_model_recommendations(baseline_model, test_data_tuples)

    cosine_sim = content_model['cosine_sim']
    content_recommendations = []
    users = raw_test_data['userId'].unique()
    
    for user in users:
        user_data = raw_test_data[raw_test_data['userId'] == user]
        
        for _, row in user_data.iterrows():
            movie_id = row['id']
            
            if movie_id not in raw_test_data['id'].values:
                continue
            
            try:
                idx = raw_test_data.index[raw_test_data['id'] == movie_id][0]
                sim_scores = list(enumerate(cosine_sim[idx]))
                sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
                sim_scores = sim_scores[1:k+1]
                
                recommended_movie_ids = [raw_test_data.iloc[i[0]]['id'] for i in sim_scores]
                content_recommendations.append((user, recommended_movie_ids))
            except IndexError:
                continue

    return {
        "svd_recommendations": svd_recommendations,
        "knn_recommendations": knn_recommendations,
        "baseline_recommendations": baseline_recommendations,
        "content_recommendations": content_recommendations
    }