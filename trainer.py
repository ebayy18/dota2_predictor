import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib
from predictor import DotaFeatureEngineer  
import warnings
warnings.filterwarnings('ignore')

if __name__ == "__main__":
    print("📥 Загрузка датасета...")
    df = pd.read_csv('matches_dataset.csv')
    print(f"✅ Загружено {len(df)} записей")
    
    # Создаём feature engineer
    feature_engineer = DotaFeatureEngineer(df)
    features_df = feature_engineer.create_match_features(df)
    
    # Разделение
    features_df = features_df.sort_values('match_id')
    split_idx = int(len(features_df) * 0.8)
    train_df = features_df.iloc[:split_idx]
    test_df = features_df.iloc[split_idx:]
    
    feature_columns = feature_engineer.get_feature_columns()
    X_train = train_df[feature_columns]
    y_train = train_df['radiant_win']
    X_test = test_df[feature_columns]
    y_test = test_df['radiant_win']
    
    # Обучение
    print("🔧 Обучение модели...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Тест
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    print(f"\n✅ Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"✅ ROC-AUC:   {roc_auc_score(y_test, y_proba):.4f}")
    
    # Сохранение
    joblib.dump({
        'model': model,
        'feature_engineer': feature_engineer,
        'feature_columns': feature_columns
    }, 'model/saved_model.pkl')
    
    print("\n💾 Модель сохранена: model/saved_model.pkl")