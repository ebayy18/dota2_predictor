import joblib
import numpy as np
import os
import pandas as pd

class DotaFeatureEngineer:
    """Создание фич только из данных ДО матча"""
    
    def __init__(self, matches_df=None):
        self.hero_stats = {}      # win rate по героям
        self.player_stats = {}    # win rate по игрокам
        self.team_stats = {}      # win rate по командам
        self.h2h_stats = {}       # история встреч команд
        
        if matches_df is not None:
            self.build_statistics(matches_df)
    
    def build_statistics(self, df):
        """Строим статистику из исторических матчей"""
        print("📊 Построение статистики...")
        
        # 1. Статистика героев
        hero_wins = {}
        hero_games = {}
        
        for _, row in df.iterrows():
            radiant_win = row['radiant_win']
            match_heroes = df[df['match_id'] == row['match_id']]
            
            for _, player in match_heroes.iterrows():
                hero_id = player['hero_id']
                is_radiant = player['is_radiant']
                
                if hero_id not in hero_games:
                    hero_games[hero_id] = 0
                    hero_wins[hero_id] = 0
                
                hero_games[hero_id] += 1
                
                if (is_radiant and radiant_win) or (not is_radiant and not radiant_win):
                    hero_wins[hero_id] += 1
        
        for hero_id in hero_games:
            self.hero_stats[hero_id] = {
                'win_rate': hero_wins[hero_id] / hero_games[hero_id] * 100,
                'games': hero_games[hero_id]
            }
        
        # 2. Статистика игроков
        player_wins = {}
        player_games = {}
        
        for _, row in df.iterrows():
            account_id = row['account_id']
            radiant_win = row['radiant_win']
            is_radiant = row['is_radiant']
            
            if account_id not in player_games:
                player_games[account_id] = 0
                player_wins[account_id] = 0
            
            player_games[account_id] += 1
            
            if (is_radiant and radiant_win) or (not is_radiant and not radiant_win):
                player_wins[account_id] += 1
        
        for account_id in player_games:
            self.player_stats[account_id] = {
                'win_rate': player_wins[account_id] / player_games[account_id] * 100,
                'games': player_games[account_id]
            }
        
        # 3. Статистика команд
        team_wins = {}
        team_games = {}
        
        for match_id in df['match_id'].unique():
            match_data = df[df['match_id'] == match_id]
            radiant_win = match_data.iloc[0]['radiant_win']
            
            radiant_team = match_data[match_data['is_radiant'] == True]['radiant_team_id'].iloc[0]
            dire_team = match_data[match_data['is_radiant'] == False]['dire_team_id'].iloc[0]
            
            if radiant_team not in team_games:
                team_games[radiant_team] = 0
                team_wins[radiant_team] = 0
            team_games[radiant_team] += 1
            if radiant_win:
                team_wins[radiant_team] += 1
            
            if dire_team not in team_games:
                team_games[dire_team] = 0
                team_wins[dire_team] = 0
            team_games[dire_team] += 1
            if not radiant_win:
                team_wins[dire_team] += 1
        
        for team_id in team_games:
            self.team_stats[team_id] = {
                'win_rate': team_wins[team_id] / team_games[team_id] * 100,
                'games': team_games[team_id]
            }
        
        # 4. H2H статистика
        for match_id in df['match_id'].unique():
            match_data = df[df['match_id'] == match_id]
            radiant_win = match_data.iloc[0]['radiant_win']
            
            radiant_team = match_data[match_data['is_radiant'] == True]['radiant_team_id'].iloc[0]
            dire_team = match_data[match_data['is_radiant'] == False]['dire_team_id'].iloc[0]
            
            h2h_key = tuple(sorted([radiant_team, dire_team]))
            
            if h2h_key not in self.h2h_stats:
                self.h2h_stats[h2h_key] = {
                    'radiant_wins': 0,
                    'dire_wins': 0,
                    'total': 0
                }
            
            self.h2h_stats[h2h_key]['total'] += 1
            if radiant_win:
                self.h2h_stats[h2h_key]['radiant_wins'] += 1
            else:
                self.h2h_stats[h2h_key]['dire_wins'] += 1
        
        print(f"✅ Героев: {len(self.hero_stats)}")
        print(f"✅ Игроков: {len(self.player_stats)}")
        print(f"✅ Команд: {len(self.team_stats)}")
        print(f"✅ H2H пар: {len(self.h2h_stats)}")
    
    def create_match_features(self, df):
        """Создаём фичи для каждого матча"""
        features_list = []
        
        for match_id in df['match_id'].unique():
            match_data = df[df['match_id'] == match_id]
            
            radiant_win = match_data.iloc[0]['radiant_win']
            radiant_team = match_data[match_data['is_radiant'] == True]['radiant_team_id'].iloc[0]
            dire_team = match_data[match_data['is_radiant'] == False]['dire_team_id'].iloc[0]
            
            radiant_heroes = match_data[match_data['is_radiant'] == True]['hero_id'].tolist()
            dire_heroes = match_data[match_data['is_radiant'] == False]['hero_id'].tolist()
            
            radiant_players = match_data[match_data['is_radiant'] == True]['account_id'].tolist()
            dire_players = match_data[match_data['is_radiant'] == False]['account_id'].tolist()
            
            radiant_team_wr = self.team_stats.get(radiant_team, {}).get('win_rate', 50)
            dire_team_wr = self.team_stats.get(dire_team, {}).get('win_rate', 50)
            team_wr_diff = radiant_team_wr - dire_team_wr
            
            radiant_hero_wr = np.mean([self.hero_stats.get(h, {}).get('win_rate', 50) for h in radiant_heroes])
            dire_hero_wr = np.mean([self.hero_stats.get(h, {}).get('win_rate', 50) for h in dire_heroes])
            hero_wr_diff = radiant_hero_wr - dire_hero_wr
            
            radiant_hero_games = np.mean([self.hero_stats.get(h, {}).get('games', 0) for h in radiant_heroes])
            dire_hero_games = np.mean([self.hero_stats.get(h, {}).get('games', 0) for h in dire_heroes])
            
            radiant_player_wr = np.mean([self.player_stats.get(p, {}).get('win_rate', 50) for p in radiant_players])
            dire_player_wr = np.mean([self.player_stats.get(p, {}).get('win_rate', 50) for p in dire_players])
            player_wr_diff = radiant_player_wr - dire_player_wr
            
            radiant_player_games = np.mean([self.player_stats.get(p, {}).get('games', 0) for p in radiant_players])
            dire_player_games = np.mean([self.player_stats.get(p, {}).get('games', 0) for p in dire_players])
            
            h2h_key = tuple(sorted([radiant_team, dire_team]))
            h2h_data = self.h2h_stats.get(h2h_key, {'radiant_wins': 0, 'dire_wins': 0, 'total': 0})
            
            if h2h_data['total'] > 0:
                h2h_radiant_wr = h2h_data['radiant_wins'] / h2h_data['total'] * 100
            else:
                h2h_radiant_wr = 50
            
            features = {
                'match_id': match_id,
                'radiant_team_id': radiant_team,
                'dire_team_id': dire_team,
                'radiant_win': radiant_win,
                'team_wr_diff': team_wr_diff,
                'hero_wr_diff': hero_wr_diff,
                'player_wr_diff': player_wr_diff,
                'radiant_hero_games': radiant_hero_games,
                'dire_hero_games': dire_hero_games,
                'radiant_player_games': radiant_player_games,
                'dire_player_games': dire_player_games,
                'h2h_radiant_wr': h2h_radiant_wr,
                'h2h_total': h2h_data['total'],
                'radiant_pick_count': len(radiant_heroes),
                'dire_pick_count': len(dire_heroes),
                'radiant_unique': len(set(radiant_heroes)),
                'dire_unique': len(set(dire_heroes)),
                'total_hero_wr': (radiant_hero_wr + dire_hero_wr) / 2,
                'total_player_wr': (radiant_player_wr + dire_player_wr) / 2,
            }
            
            features_list.append(features)
        
        return pd.DataFrame(features_list)
    
    def get_feature_columns(self):
        """Список фич для модели"""
        return [
            'team_wr_diff',
            'hero_wr_diff',
            'player_wr_diff',
            'radiant_hero_games',
            'dire_hero_games',
            'radiant_player_games',
            'dire_player_games',
            'h2h_radiant_wr',
            'h2h_total',
            'radiant_pick_count',
            'dire_pick_count',
            'radiant_unique',
            'dire_unique',
            'total_hero_wr',
            'total_player_wr'
        ]


class DotaPredictor:
    """Класс для загрузки модели и предсказаний"""
    
    def __init__(self):
        self.model = None
        self.feature_engineer = None
        self.feature_columns = None
        self.is_loaded = False
    
    def load(self, filepath='model/saved_model.pkl'):
        """Загрузка обученной модели"""
        try:
            if not os.path.exists(filepath):
                print(f"❌ Файл модели не найден: {filepath}")
                print("💡 Сначала обучите модель: python model/trainer.py")
                return False
            
            print(f"📥 Загрузка модели из {filepath}...")
            data = joblib.load(filepath)
            
            self.model = data['model']
            self.feature_engineer = data['feature_engineer']
            self.feature_columns = data['feature_columns']
            self.is_loaded = True
            
            print(f"✅ Модель загружена успешно!")
            print(f"   - Тип модели: {type(self.model).__name__}")
            print(f"   - Количество фич: {len(self.feature_columns)}")
            print(f"   - Героев в базе: {len(self.feature_engineer.hero_stats)}")
            print(f"   - Игроков в базе: {len(self.feature_engineer.player_stats)}")
            print(f"   - Команд в базе: {len(self.feature_engineer.team_stats)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            import traceback
            traceback.print_exc()
            self.is_loaded = False
            return False
    
    def predict_match(self, radiant_team_id, dire_team_id, radiant_heroes, dire_heroes,
                  radiant_players=None, dire_players=None):
        """Предсказание исхода матча"""
        
        if not self.is_loaded:
            raise ValueError("Модель не загружена! Вызовите load() сначала.")
        
        if not radiant_heroes or not dire_heroes:
            raise ValueError("Списки героев не могут быть пустыми!")
        
        # === ИЗВЛЕКАЕМ СТАТИСТИКУ ===
        radiant_team_wr = self.feature_engineer.team_stats.get(radiant_team_id, {}).get('win_rate', 50)
        dire_team_wr = self.feature_engineer.team_stats.get(dire_team_id, {}).get('win_rate', 50)
        
        radiant_hero_wr = np.mean([
            self.feature_engineer.hero_stats.get(h, {}).get('win_rate', 50) 
            for h in radiant_heroes
        ])
        dire_hero_wr = np.mean([
            self.feature_engineer.hero_stats.get(h, {}).get('win_rate', 50) 
            for h in dire_heroes
        ])
        
        radiant_hero_games = np.mean([
            self.feature_engineer.hero_stats.get(h, {}).get('games', 0) 
            for h in radiant_heroes
        ])
        dire_hero_games = np.mean([
            self.feature_engineer.hero_stats.get(h, {}).get('games', 0) 
            for h in dire_heroes
        ])
        
        if radiant_players and dire_players:
            radiant_player_wr = np.mean([
                self.feature_engineer.player_stats.get(p, {}).get('win_rate', 50) 
                for p in radiant_players
            ])
            dire_player_wr = np.mean([
                self.feature_engineer.player_stats.get(p, {}).get('win_rate', 50) 
                for p in dire_players
            ])
            
            radiant_player_games = np.mean([
                self.feature_engineer.player_stats.get(p, {}).get('games', 0) 
                for p in radiant_players
            ])
            dire_player_games = np.mean([
                self.feature_engineer.player_stats.get(p, {}).get('games', 0) 
                for p in dire_players
            ])
        else:
            radiant_player_wr = 50
            dire_player_wr = 50
            radiant_player_games = 0
            dire_player_games = 0
        
        # H2H статистика
        h2h_key = tuple(sorted([radiant_team_id, dire_team_id]))
        h2h_data = self.feature_engineer.h2h_stats.get(h2h_key, {'radiant_wins': 0, 'total': 0})
        
        if h2h_data['total'] > 0:
            h2h_radiant_wr = h2h_data['radiant_wins'] / h2h_data['total'] * 100
        else:
            h2h_radiant_wr = 50
        
        # === СОЗДАЁМ ФЕЧИ ===
        features = {
            'team_wr_diff': radiant_team_wr - dire_team_wr,
            'hero_wr_diff': radiant_hero_wr - dire_hero_wr,
            'player_wr_diff': radiant_player_wr - dire_player_wr,
            'radiant_hero_games': radiant_hero_games,
            'dire_hero_games': dire_hero_games,
            'radiant_player_games': radiant_player_games,
            'dire_player_games': dire_player_games,
            'h2h_radiant_wr': h2h_radiant_wr,
            'h2h_total': h2h_data['total'],
            'radiant_pick_count': len(radiant_heroes),
            'dire_pick_count': len(dire_heroes),
            'radiant_unique': len(set(radiant_heroes)),
            'dire_unique': len(set(dire_heroes)),
            'total_hero_wr': (radiant_hero_wr + dire_hero_wr) / 2,
            'total_player_wr': (radiant_player_wr + dire_player_wr) / 2
        }
        
        # === ПРЕДСКАЗАНИЕ (ИСПРАВЛЕНО) ===
        import pandas as pd
        X = pd.DataFrame([[features[col] for col in self.feature_columns]], columns=self.feature_columns)
        
        print(f"🔮 Features: {features}")
        print(f"🔮 X shape: {X.shape}")
        print(f"🔮 X columns: {X.columns.tolist()}")
        
        try:
            proba = self.model.predict_proba(X)[0]
            print(f"✅ Prediction probabilities: {proba}")
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            raise e
        
        radiant_win_prob = proba[1] * 100
        dire_win_prob = proba[0] * 100
        
        winner = 'radiant' if radiant_win_prob > dire_win_prob else 'dire'
        confidence = max(radiant_win_prob, dire_win_prob)
        
        # === ФОРМИРУЕМ РЕЗУЛЬТАТ ===
        result = {
            'radiant_win_chance': round(radiant_win_prob, 1),
            'dire_win_chance': round(dire_win_prob, 1),
            'winner': winner,
            'confidence': round(confidence, 1),
            'factors': {
                'team_wr_diff': round(features['team_wr_diff'], 1),
                'hero_wr_diff': round(features['hero_wr_diff'], 1),
                'player_wr_diff': round(features['player_wr_diff'], 1),
                'h2h_radiant_wr': round(features['h2h_radiant_wr'], 1),
                'h2h_matches': features['h2h_total']
            },
            'team_stats': {
                'radiant': {
                    'team_wr': round(radiant_team_wr, 1),
                    'hero_wr': round(radiant_hero_wr, 1),
                    'player_wr': round(radiant_player_wr, 1) if radiant_players else None
                },
                'dire': {
                    'team_wr': round(dire_team_wr, 1),
                    'hero_wr': round(dire_hero_wr, 1),
                    'player_wr': round(dire_player_wr, 1) if dire_players else None
                }
            }
        }
        
        return result
