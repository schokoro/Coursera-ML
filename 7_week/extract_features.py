#!/usr/bin/env python

import bz2
import json
import pandas
import collections
import argparse
import os
import math


class Table:

    def __init__(self, matches_filename, time=300):
        if not os.path.isfile(matches_filename):
            raise FileNotFoundError
        self.df = self.create_dfdict()
        self.max_id = 0
        self.numeric = []
        self.dummies = []
        self.matches_filename = matches_filename
        self.time = time
        # итог матча (отсутствует в тестовых матчах)


    def create_dfdict(self):
        self.num_bool = ['match_id', 'start_time', 'lobby_type', 'first_blood_time', 'first_blood_team',
                    'first_blood_player1', 'first_blood_player2', 'radiant_bottle_time', 'radiant_courier_time',
                    'radiant_flying_courier_time','radiant_tpscroll_count', 'radiant_boots_count',
                    'radiant_ward_observer_count', 'radiant_ward_sentry_count', 'radiant_first_ward_time',
                    'dire_bottle_time', 'dire_courier_time', 'dire_flying_courier_time', 'dire_tpscroll_count',
                    'dire_boots_count', 'dire_ward_observer_count', 'dire_ward_sentry_count', 'dire_first_ward_time',
                     'radiant_win']
        return {key: [] for key in self.num_bool}

    def last_value(self, series, times):
        values = [v for t, v in zip(times, series) if t <= self.time]
        return values[-1] if len(values) > 0 else 0

    def filter_events(self, events):
        return [event for event in events if event['time'] <= self.time]

    def extend(self, max_id):
        for i in range(self.max_id+1, max_id+1):
            ll = len(self.df['match_id'])
            self.df[str(i) + '_hero'] = [0] * ll
            self.df[str(i) + '_level'] = [0] * ll
            self.df[str(i) + '_xp'] = [0] * ll
            self.df[str(i) + '_gold'] = [0] * ll
            self.df[str(i) + '_lh'] = [0] * ll
            self.df[str(i) + '_kills'] = [0] * ll
            self.df[str(i) + '_deaths'] = [0] * ll
            self.df[str(i) + '_items'] = [0] * ll

    def get_df(self):
        return pandas.DataFrame.from_records(self.df).set_index('match_id').sort_index()

    def extract(self):
        for match in self.iterate_matches():
            self.match_proceed(match)
        print('The end of extraction')

    def match_proceed(self, match):

        users = {player['hero_id']: i for i, player in enumerate(match['players'])}
        max_id = max(users.keys())
        if max_id > self.max_id:
            self.extend(max_id)
            self.max_id = max_id
        times = match['times']
        players = match['players']
        for player_id in range(1, self.max_id + 1):
            self.df[str(player_id) + '_hero'].append(
                (int(math.copysign(1, 4.5 - users[player_id])) if player_id in users else 0))#
            self.df[str(player_id) + '_level'].append(
                (self.last_value(players[users[player_id]]['gold_t'], times) if player_id in users else 0))#
            self.df[str(player_id) + '_xp'].append(
                (self.last_value(players[users[player_id]]['xp_t'], times) if player_id in users else 0))#
            self.df[str(player_id) + '_gold'].append(
                (self.last_value(players[users[player_id]]['gold_t'], times) if player_id in users else 0))#
            self.df[str(player_id) + '_lh'].append(
                (self.last_value(players[users[player_id]]['lh_t'], times) if player_id in users else 0))#
            self.df[str(player_id) + '_kills'].append(
                (len(self.filter_events(players[users[player_id]]['kills_log'])) if player_id in users else 0))#
            self.df[str(player_id) + '_deaths'].append(
                (self.last_value(players[users[player_id]]['gold_t'], times) if player_id in users else 0))
            self.df[str(player_id) + '_items'].append(
                (self.last_value(players[users[player_id]]['gold_t'], times) if player_id in users else 0))

        for param in self.num_bool:
            self.df[param].append(match['match_id'])

    def iterate_matches(self):
        with bz2.BZ2File(self.matches_filename) as f:
            for n, line in enumerate(f):
                match = json.loads(line)
                yield match
                if (n + 1) % 1000 == 0:
                    # break
                    print('Processed %d matches' % (n+1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract features from matches data')
    parser.add_argument('input_matches')
    parser.add_argument('output_csv')
    parser.add_argument('--time', type=int, default=5*60)
    args = parser.parse_args()
    try:
        table: Table = Table(args.input_matches, args.time)
        table.extract()
        features_table = table.get_df()
        features_table.to_csv(args.output_csv)
    except FileNotFoundError:
        print(f'Файл {args.input_matches} не существует')
