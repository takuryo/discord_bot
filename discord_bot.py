#! python3

import discord
import datetime
import json
import requests

# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('起動しました')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    with open('setting_con.json') as con:
        set_con = json.load(con)
    with open('setting_var.json') as var:
        set_var = json.load(var)
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # 役職確認
    for role in message.author.roles:
        if str(role) == set_con['role_unei']:
            set_var['role_flag'] = 1
        elif str(role) == set_con['role_ban']:
            set_var['role_flag'] = 2
        else:
            set_var['role_flag'] = 3
    # ?create 引数の名前の大会を作成
    if message.content.startswith('?create'):
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        elif len(message.content.split()) != 2:
            await message.channel.send('トーナメント名が指定されていないか、使用不可能な文字が含まれています。')
        elif set_var['create_flag'] == True:
            await message.channel.send('大会はすでに作成されています。')
        else:
            tounament_name = message.content.split()[1]
            dt_now = datetime.datetime.today()
            set_var['tounament_URL'] = 'Mockbattle_tounament_' + dt_now.strftime('%Y%m%d_%H%M%S')
            make_json = {'api_key': set_con['api_key'], 'tournament': {
                'name': tounament_name, 'url': set_var['tounament_URL'], 'hold_third_place_match': True}}
            create_url = "https://api.challonge.com/v1/tournaments.json"
            create_result = requests.post(create_url, json.dumps(
                make_json), headers={'Content-Type': 'application/json'})
            if str(create_result.json) != set_con['check_responce']:
                await message.channel.send('トーナメントの作成に失敗しました。')
            else:
                await message.channel.send(tounament_name + 'を作成しました。\n' + 'https://challonge.com/ja/' + set_var['tounament_URL'])
                set_var['create_flag'] = True
                set_var['open_flag'] = True
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)

    # ?join 参加処理
    if message.content.startswith('?join') and set_var['create_flag'] == True:
        if len(message.content.split()) != 2:
            await message.channel.send('参加者名が指定されていないか、使用不可能な文字が含まれています。')
        else:
            name = message.content.split()[1]
            with open('participant_list.json') as par:
                par_list = json.load(par)
            name_array = [i.get('name') for i in par_list]
            #id_dis = [i.get('id_dis') for i in par_list]
            id_tou = [i.get('id_tou') for i in par_list]

            if set_var['role_flag'] == 2:
                await message.channel.send('あなたはペナルティにより大会参加不可です。')
            elif set_var['open_flag'] == False:
                await message.channel.send('参加受付は終了しています')
            elif name in name_array:
                await message.channel.send('同名の参加者がいます。名前を変更してください。')
            #elif message.author.id in id_dis:
            #    await message.channel.send(name + 'さんは既に参加しています。')
            else:
                join_json = {'api_key': set_con['api_key'], 'participant': {'name': name}}
                join_url = "https://api.challonge.com/v1/tournaments/" + \
                    set_var['tounament_URL'] + "/participants.json"
                join_result = requests.post(join_url, json.dumps(join_json), headers={
                                            'Content-Type': 'application/json'})
                join_data = json.loads(join_result.text)
                if str(join_result.json) != set_con['check_responce']:
                    await message.channel.send('操作は実行されませんでした。')
                else:
                    par_dict = {'name':name, 'id_dis': message.author.id, 'id_tou':join_data['participant']['id']}
                    par_list.append(par_dict)
                    await message.channel.send(name + 'さんの参加を認証しました。')
                    with open('participant_list.json', 'w') as par:
                        json.dump(par_list, par, indent=2, ensure_ascii=False)

    # ?delete 参加取り消し
    if message.content.startswith('?delete') and set_var['create_flag'] == True:
        if len(message.content.split()) != 2:
            await message.channel.send('参加者名が指定されていないか、使用不可能な文字が含まれています。')
        elif set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        else:
            with open('participant_list.json') as par:
                par_list = json.load(par)
            name_array = [i.get('name') for i in par_list]
            id_dis = [i.get('id_dis') for i in par_list]
            id_tou = [i.get('id_tou') for i in par_list]
            if set_var['open_flag'] == False:
                await message.channel.send('参加取り消しの受付は終了しています。')
            #elif message.author.id not in id_dis:
            #    await message.channel.send('あなたはまだ参加していません。')
            else:
                for i in range(len(name_array)):
                    if(name_array[i] == str(message.content.split()[1])):
                        index = i
                        break
                delete_json = {'api_key': set_con['api_key']}
                delete_url = "https://api.challonge.com/v1/tournaments/" + \
                    set_var['tounament_URL'] + "/participants/" + str(id_tou[index]) + ".json"
                delete_result = requests.delete(delete_url, data=json.dumps(
                    delete_json), headers={'Content-Type': 'application/json'})
                if str(delete_result.json) != set_con['check_responce']:
                    await message.channel.send('操作は実行されませんでした。')
                else:
                    par_list.pop(index)
                    await message.channel.send(name_array[index] + 'さんの参加を取り消しました。')
                    with open('participant_list.json', 'w') as par:
                        json.dump(par_list, par, indent=2, ensure_ascii=False)

    # ?close 参加受付終了
    if message.content == '?close' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        elif set_var['open_flag'] == True:
            await message.channel.send('参加受付を終了します。')
            set_var['open_flag'] = False
            with open('setting_var.json', 'w') as var:
                json.dump(set_var, var, indent=2, ensure_ascii=False)
        elif set_var['open_flag'] == False:
            await message.channel.send('すでに参加受付を終了しています。')

    # ?open 参加受付開始
    if message.content == '?open' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        elif set_var['open_flag'] == False:
            await message.channel.send('参加受付を再開します。')
            set_var['open_flag'] = True
            with open('setting_var.json', 'w') as var:
                json.dump(set_var, var, indent=2, ensure_ascii=False)
        elif set_var['open_flag'] == True:
            await message.channel.send('すでに参加受付は開始されています。')

    # ?shuffle 組み合わせランダム入れ替え
    if message.content == '?shuffle' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        else:
            shuffle_json = {'api_key': set_con['api_key']}
            shuffle_url = 'https://api.challonge.com/v1/tournaments/' + \
                set_var['tounament_URL'] + '/participants/randomize.json'
            shuffle_result = requests.post(shuffle_url, json.dumps(
                shuffle_json), headers={'Content-Type': 'application/json'})
            if str(shuffle_result.json) != set_con['check_responce']:
                await message.channel.send('操作は実行されませんでした。')
            else:
                await message.channel.send('組み合わせをシャッフルしました。')

    # ?start 大会開始
    if message.content == '?start' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        else:
            start_json = {'api_key': set_con['api_key']}
            start_url = 'https://api.challonge.com/v1/tournaments/' + \
                set_var['tounament_URL'] + '/start.json'
            start_result = requests.post(start_url, json.dumps(start_json), headers={
                        'Content-Type': 'application/json'})
            if str(start_result.json) != set_con['check_responce']:
                await message.channel.send('操作は実行されませんでした。')
            else:
                set_var['open_flag'] = False
                await message.channel.send('大会を開始しました。\n' + 'https://challonge.com/ja/' + set_var['tounament_URL'])
                with open('participant_list.json') as par:
                    par_list = json.load(par)
                name_array = [i.get('name') for i in par_list]
                id_dis = [i.get('id_dis') for i in par_list]
                id_tou = [i.get('id_tou') for i in par_list]
                call_url = 'https://api.challonge.com/v1/tournaments/' + \
                    set_var['tounament_URL'] + '/matches.json?api_key=' + set_con['api_key']
                call_result = requests.get(
                    call_url, headers={'Content-Type': 'application/json'})
                call_data = json.loads(call_result.text)
                set_var['first_match_id'] = call_data[0]['match']['id']
                for index in range(len(id_tou)):
                    if call_data[0]['match']['player1_id'] == id_tou[index]:
                        pl1_index = index
                    elif call_data[0]['match']['player2_id'] == id_tou[index]:
                        pl2_index = index
                await message.channel.send('第一試合は' + str(name_array[pl1_index]) + 'さんと' + str(name_array[pl2_index]) + 'さんです。\n対戦準備をお願いします。')
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)

    # ?call メンションで呼び出し,引数がある場合その番号の試合を呼び出し
    if message.content.startswith('?call') and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        else:
            if message.content != '?call':
                call_url = 'https://api.challonge.com/v1/tournaments/' + set_var['tounament_URL'] + '/matches/' + str(set_var['first_match_id'] + int(message.content[6:]) - 1) + '.json?api_key=' + set_con['api_key']
            else:
                call_url = 'https://api.challonge.com/v1/tournaments/' + set_var['tounament_URL'] + '/matches/' + str(set_var['first_match_id'] + set_var['now_match_count']) + '.json?api_key=' + set_con['api_key']
                set_var['now_match_count'] += 1
            call_result = requests.get(
                call_url, headers={'Content-Type': 'application/json'})
            if str(call_result.json) != set_con['check_responce']:
                await message.channel.send('対戦情報を取得できませんでした。')
            else:
                with open('participant_list.json') as par:
                    par_list = json.load(par)
                name_array = [i.get('name') for i in par_list]
                id_dis = [i.get('id_dis') for i in par_list]
                id_tou = [i.get('id_tou') for i in par_list]
                call_data = json.loads(call_result.text)
                for index in range(len(id_tou)):
                    if call_data['match']['player1_id'] == id_tou[index]:
                        pl1_index = index
                    elif call_data['match']['player2_id'] == id_tou[index]:
                        pl2_index = index
                #await message.channel.send('<@' + str(id_dis[pl1_index]) + '>さん、<@' + str(id_dis[pl2_index]) + '>さん、試合を開始してください。')
                await message.channel.send(name_array[pl1_index] + 'さん、' + name_array[pl2_index] +'さん、試合を開始してください。')
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)

    # ?finalize 大会終了
    if message.content == '?finalize' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        else:
            finalize_json = {'api_key': set_con['api_key']}
            finalize_url = 'https://api.challonge.com/v1/tournaments/' + \
                set_var['tounament_URL'] + '/finalize.json'
            finalize_result = requests.post(finalize_url, json.dumps(finalize_json),
                        headers={'Content-Type': 'application/json'})
            if str(finalize_result.json) != set_con['check_responce']:
                await message.channel.send('操作は実行されませんでした。')
            else:
                await message.channel.send('大会を終了しました。')
                # 初期化
                set_var = {"create_flag": False,"open_flag": False,"role_flag": 3,"first_match_id": 0,"now_match_count": 0,"tounament_URL": ""}
                par_list = [{"name": "","id_dis": 0,"id_tou": 0}]
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)
                with open('participant_list.json', 'w') as par:
                    json.dump(par_list, par, indent=2, ensure_ascii=False)

    # ?reset 中止時の初期化コマンドの作成
    if message.content == '?reset':
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
        else:
            set_var = {"create_flag": False,"open_flag": False,"role_flag": 3,"first_match_id": 0,"now_match_count": 0,"tounament_URL": ""}
            par_list = [{"name": "","id_dis": 0,"id_tou": 0}]
            with open('setting_var.json', 'w') as var:
                json.dump(set_var, var, indent=2, ensure_ascii=False)
            with open('participant_list.json', 'w') as par:
                json.dump(par_list, par, indent=2, ensure_ascii=False)
            await message.channel.send('内部データをリセットしました。')

# Botの起動とDiscordサーバーへの接続
with open('setting_con.json') as con:
    set_con = json.load(con)
client.run(set_con['TOKEN'])
