#! python3

import datetime
import json

import discord
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
    if message.channel.id not in set_con['channel_allowed']:
        return
    # 役職確認
    for role in message.author.roles:
        if str(role) in set_con['role_unei']:
            set_var['role_flag'] = 1
        elif str(role) == set_con['role_ban']:
            set_var['role_flag'] = 2
        else:
            set_var['role_flag'] = 3
    # ?create 引数の名前の大会を作成
    if message.content.startswith('?create'):
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif len(message.content.split()) != 2:
            embed = discord.Embed(title='Error 102', description='名称が指定されていないか、使用不可能な文字が含まれています。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif set_var['create_flag'] == True:
            embed = discord.Embed(title='Error 201', description='トーナメントはすでに作成されています。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            tounament_name = message.content.split()[1]
            dt_now = datetime.datetime.today()
            set_var['tounament_URL'] = 'Mockbattle_tounament_' + dt_now.strftime('%Y%m%d_%H%M%S')
            make_json = {'api_key': set_con['api_key'], 'tournament': {
                'name': tounament_name, 'url': set_var['tounament_URL'], 'hold_third_place_match': True,'show_rounds':False ,'game_name':''}}
            create_url = "https://api.challonge.com/v1/tournaments.json"
            create_result = requests.post(create_url, json.dumps(
                make_json), headers={'Content-Type': 'application/json'})
            if str(create_result.json) != set_con['check_responce']:
                embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                await message.channel.send(embed=embed)
            else:
                desc = tounament_name + 'を作成しました。\n' + 'https://challonge.com/ja/' + set_var['tounament_URL']
                embed = discord.Embed(title='大会作成', description=desc, color=0x00ff00)
                await message.channel.send(embed=embed)
                set_var['create_flag'] = True
                set_var['open_flag'] = True
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)

    # ?join 参加処理
    if message.content.startswith('?join') and set_var['create_flag'] == True:
        if len(message.content.split()) != 2:
            embed = discord.Embed(title='Error 102', description='名称が指定されていないか、使用不可能な文字が含まれています。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            name = message.content.split()[1]
            with open('participant_list.json') as par:
                par_list = json.load(par)
            name_array = [i.get('name') for i in par_list]
            id_dis = [i.get('id_dis') for i in par_list]
            id_tou = [i.get('id_tou') for i in par_list]

            if set_var['role_flag'] == 2:
                embed = discord.Embed(title='Error 301', description='あなたはペナルティにより参加不可能です。', color=0xff0000)
                await message.channel.send(embed=embed)
            elif set_var['open_flag'] == False:
                embed = discord.Embed(title='Error 302', description='参加受付は終了しています。', color=0xff0000)
                await message.channel.send(embed=embed)
            elif name in name_array:
                embed = discord.Embed(title='Error 304', description='同名の参加者がいます。名前を変更してください。', color=0xff0000)
                await message.channel.send(embed=embed)
            #elif message.author.id in id_dis:
            #    embed = discord.Embed(title='Error 305', description='あなたはすでに参加しています', color=0xff0000)
            #    await message.channel.send(embed=embed)
            else:
                join_json = {'api_key': set_con['api_key'], 'participant': {'name': name}}
                join_url = set_con['rq_url'] + set_var['tounament_URL'] + "/participants.json"
                join_result = requests.post(join_url, json.dumps(join_json), headers={
                                            'Content-Type': 'application/json'})
                join_data = json.loads(join_result.text)
                if str(join_result.json) != set_con['check_responce']:
                    embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                    await message.channel.send(embed=embed)
                else:
                    par_dict = {'name':name, 'id_dis': message.author.id, 'id_tou':join_data['participant']['id']}
                    par_list.append(par_dict)
                    desc = '<@' + str(message.author.id) + '>さんの参加を認証しました。'
                    embed = discord.Embed(title='参加', description=desc, color=0x00ff00)
                    await message.channel.send(embed=embed)
                    #await message.author.add_roles(message.guild.get_role(set_con['roleID_participant']))
                    with open('participant_list.json', 'w') as par:
                        json.dump(par_list, par, indent=2, ensure_ascii=False)

    # ?delete 参加取り消し
    if message.content.startswith('?delete') and set_var['create_flag'] == True:
        with open('participant_list.json') as par:
            par_list = json.load(par)
        name_array = [i.get('name') for i in par_list]
        id_dis = [i.get('id_dis') for i in par_list]
        id_tou = [i.get('id_tou') for i in par_list]
        if len(message.content.split()) != 1 and len(message.content.split()) != 2:
            embed = discord.Embed(title='Error 102', description='名称が指定されていないか、使用不可能な文字が含まれています。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif len(message.content.split()) == 2 and set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif len(message.content.split()) == 1 and set_var['open_flag'] == False:
            embed = discord.Embed(title='Error 303', description='参加取り消しの受付は終了しています。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif len(message.content.split()) == 1 and message.author.id not in id_dis:
            embed = discord.Embed(title='Error 306', description='参加取り消しの受付は終了しています。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            if len(message.content.split()) == 1:
                for i in range(len(id_dis)):
                    if(id_dis[i] == message.author.id):
                        index = i
                        break
            else:
                for i in range(len(name_array)):
                    if name_array[i] == message.content.split()[1]:
                        index = i
                        break
                    elif i == len(name_array):
                        embed = discord.Embed(title='Error 307', description='指定された参加者は存在しません。', color=0xff0000)
                        await message.channel.send(embed=embed)
                        return
            delete_player_id = id_tou[index]
            delete_json = {'api_key': set_con['api_key']}
            delete_url = set_con['rq_url'] + set_var['tounament_URL'] + "/participants/" + str(id_tou[index]) + ".json"
            delete_result = requests.delete(delete_url, data=json.dumps(
                delete_json), headers={'Content-Type': 'application/json'})
            if str(delete_result.json) != set_con['check_responce']:
                embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                await message.channel.send(embed=embed)
            else:
                desc = '<@' + str(id_dis[index]) + '>さんの参加を取り消しました。'
                embed = discord.Embed(title='参加取り消し', description=desc, color=0x00ff00)
                await message.channel.send(embed=embed)
                par_list.pop(index)
                #await message.author.remove_roles(message.guild.get_role(set_con['roleID_participant']))
                with open('participant_list.json', 'w') as par:
                    json.dump(par_list, par, indent=2, ensure_ascii=False)

    # ?close 参加受付終了
    if message.content == '?close' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif set_var['open_flag'] == True:
            embed = discord.Embed(title='受付終了', description='参加受付を終了します。', color=0x00ff00)
            await message.channel.send(embed=embed)
            set_var['open_flag'] = False
            with open('setting_var.json', 'w') as var:
                json.dump(set_var, var, indent=2, ensure_ascii=False)
        elif set_var['open_flag'] == False:
            embed = discord.Embed(title='Error 401', description='すでに参加受付を終了しています。', color=0xff0000)
            await message.channel.send(embed=embed)

    # ?open 参加受付開始
    if message.content == '?open' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        elif set_var['open_flag'] == False:
            embed = discord.Embed(title='受付再開', description='参加受付を再開します。', color=0x00ff00)
            await message.channel.send(embed=embed)
            set_var['open_flag'] = True
            with open('setting_var.json', 'w') as var:
                json.dump(set_var, var, indent=2, ensure_ascii=False)
        elif set_var['open_flag'] == True:
            embed = discord.Embed(title='Error 402', description='すでに参加受付を終了しています。', color=0xff0000)
            await message.channel.send(embed=embed)

    # ?shuffle 組み合わせランダム入れ替え
    if message.content == '?shuffle' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            shuffle_json = {'api_key': set_con['api_key']}
            shuffle_url = set_con['rq_url'] + set_var['tounament_URL'] + '/participants/randomize.json'
            shuffle_result = requests.post(shuffle_url, json.dumps(
                shuffle_json), headers={'Content-Type': 'application/json'})
            if str(shuffle_result.json) != set_con['check_responce']:
                embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='順番入れ替え', description='組み合わせをシャッフルしました。', color=0x00ff00)
                await message.channel.send(embed=embed)

    # ?start 大会開始
    if message.content == '?start' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            start_json = {'api_key': set_con['api_key']}
            start_url = set_con['rq_url'] + set_var['tounament_URL'] + '/start.json'
            start_result = requests.post(start_url, json.dumps(start_json), headers={
                        'Content-Type': 'application/json'})
            if str(start_result.json) != set_con['check_responce']:
                embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                await message.channel.send(embed=embed)
            else:
                set_var['open_flag'] = False
                with open('participant_list.json') as par:
                    par_list = json.load(par)
                name_array = [i.get('name') for i in par_list]
                id_dis = [i.get('id_dis') for i in par_list]
                id_tou = [i.get('id_tou') for i in par_list]
                set_var['participant_num'] = len(name_array) - 1
                call_url = set_con['rq_url'] + set_var['tounament_URL'] + '/matches.json?api_key=' + set_con['api_key']
                call_result = requests.get(
                    call_url, headers={'Content-Type': 'application/json'})
                call_data = json.loads(call_result.text)
                set_var['first_match_id'] = call_data[0]['match']['id']
                for index in range(len(id_tou)):
                    if call_data[0]['match']['player1_id'] == id_tou[index]:
                        pl1_index = index
                    elif call_data[0]['match']['player2_id'] == id_tou[index]:
                        pl2_index = index
                desc = '大会を開始しました。\n' + 'https://challonge.com/ja/' + set_var['tounament_URL'] + '\n第一試合は<@' + str(id_dis[pl1_index]) + '>さんと<@' + str(id_dis[pl2_index]) + '>さんです。\n対戦準備をお願いします。'
                embed = discord.Embed(title='大会開始', description=desc, color=0x00ff00)
                await message.channel.send(embed=embed)
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)

    # ?call メンションで呼び出し,引数がある場合その番号の試合を呼び出し
    if message.content.startswith('?call') and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            if len(message.content.split()) == 1:
                call_url = set_con['rq_url'] + set_var['tounament_URL'] + '/matches/' + str(set_var['first_match_id'] + set_con['match_id'][set_var['participant_num'] - 1][set_var['now_match_count']] - 1)  + '.json?api_key=' + set_con['api_key']
                set_var['now_match_count'] += 1
            elif len(message.content.split()) == 2:
                call_url = set_con['rq_url'] + set_var['tounament_URL'] + '/matches/' + str(set_var['first_match_id'] + message.content.split()[1] - 1) + '.json?api_key=' + set_con['api_key']
            else:
                embed = discord.Embed(title='Error 601', description='形式が誤っています。', color=0xff0000)
                await message.channel.send(embed=embed)
            call_result = requests.get(
                call_url, headers={'Content-Type': 'application/json'})
            if str(call_result.json) != set_con['check_responce']:
                embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                await message.channel.send(embed=embed)
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
                desc1 = '<@' + str(id_dis[pl1_index]) + '>'
                desc2 = '<@' + str(id_dis[pl2_index]) + '>'
                title = '第' + str(set_var['now_match_count']) +'試合'
                embed = discord.Embed(title=title, description='以下2名の試合を開始してください。', color=0x00ff00)
                embed.add_field(name = 'player1',value=desc1, inline=True)
                embed.add_field(name = 'player2',value=desc2, inline=True)
                await message.channel.send(embed=embed)
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)
    # ?score 結果入力
    if message.content.startswith('?score') and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            await message.channel.send('あなたはこのコマンドを実行する権限がありません。')
            return
        #if len(message.content.split())

    # ?finalize 大会終了
    if message.content == '?finalize' and set_var['create_flag'] == True:
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            finalize_json = {'api_key': set_con['api_key']}
            finalize_url = set_con['rq_url'] + set_var['tounament_URL'] + '/finalize.json'
            finalize_result = requests.post(finalize_url, json.dumps(finalize_json),
                        headers={'Content-Type': 'application/json'})
            if str(finalize_result.json) != set_con['check_responce']:
                embed = discord.Embed(title='Error 103', description='通信に失敗しました。', color=0xff0000)
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='大会終了', description='大会を終了しました。', color=0x00ff00)
                await message.channel.send(embed=embed)
                # 初期化
                set_var = {"create_flag": False,"open_flag": False,"role_flag": 3,"first_match_id": 0,"now_match_count": 0,"tounament_URL": "","participant_num": 0}
                par_list = [{"name": "","id_dis": 0,"id_tou": 0}]
                with open('setting_var.json', 'w') as var:
                    json.dump(set_var, var, indent=2, ensure_ascii=False)
                with open('participant_list.json', 'w') as par:
                    json.dump(par_list, par, indent=2, ensure_ascii=False)

    # ?reset 中止時の初期化コマンドの作成
    if message.content == '?reset':
        if set_var['role_flag'] != 1:
            embed = discord.Embed(title='Error 101', description='実行権限がありません。', color=0xff0000)
            await message.channel.send(embed=embed)
        else:
            reset_json = {'api_key': set_con['api_key']}
            reset_url = set_con['rq_url'] + set_var['tounament_URL'] + ".json"
            requests.delete(reset_url, data=json.dumps(
                reset_json), headers={'Content-Type': 'application/json'})
            set_var = {"create_flag": False,"open_flag": False,"role_flag": 3,"first_match_id": 0,"now_match_count": 0,"tounament_URL": "","participant_num": 0}
            par_list = [{"name": "","id_dis": 0,"id_tou": 0}]
            with open('setting_var.json', 'w') as var:
                json.dump(set_var, var, indent=2, ensure_ascii=False)
            with open('participant_list.json', 'w') as par:
                json.dump(par_list, par, indent=2, ensure_ascii=False)
            embed = discord.Embed(title='大会途中終了', description='大会を途中終了しました。', color=0x00ff00)
            await message.channel.send(embed=embed)
    
    # <管理者用> 役職付与
    if message.content.startswith('?role'):
        if len(message.content.split()) != 2:
            await message.channel.send('形式が異なるか、使用不可能な文字が含まれています。')
        elif message.author.id not in set_con['uneiperson_id']:
            await message.channel.send('このコマンドは特定のユーザーのみ実行可能です。')
        else:
            if message.content.split()[1] == 'add':
                await message.author.add_roles(message.guild.get_role(set_con['roleID_unei']))
            elif message.content.split()[1] == 'remove':
                await message.author.remove_roles(message.guild.get_role(set_con['roleID_unei']))

# Botの起動とDiscordサーバーへの接続
with open('setting_con.json') as con:
    set_con = json.load(con)
client.run('')
