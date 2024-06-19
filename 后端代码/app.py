# import caching as caching
from matplotlib.colors import LinearSegmentedColormap, to_rgba
import matplotlib.colors as colors
from flask import Flask, jsonify, request
from sqlalchemy import text
import matplotlib.pyplot as plt
from config import BaseConfig
from flask_sqlalchemy import SQLAlchemy
import auth
# from aliyunsms.sms_send import send_sms
# import json
# import random
import io
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
# from redis import StrictRedis


# # 创建redis对象
# redis_store = StrictRedis(host=BaseConfig.REDIS_HOST, port=BaseConfig.REDIS_PORT, decode_responses=True)

# 跨域
from flask_cors import CORS
from flask_cors import cross_origin


app = Flask(__name__)

# 添加配置数据库
app.config.from_object(BaseConfig)
# 初始化拓展,app到数据库的ORM映射
db = SQLAlchemy(app)

# 检查数据库连接是否成功
with app.app_context():
    with db.engine.connect() as conn:

        cols = conn.execute(text("SELECT COLUMN_NAME\
                          FROM INFORMATION_SCHEMA.COLUMNS\
                          WHERE TABLE_SCHEMA='Ocean_Front'\
                          AND TABLE_NAME='user'")).fetchall()
        cols = [i[0] for i in cols]
        rs = conn.execute(text("select 1"))
        print(rs.fetchone())
        # print(cols)


def get_token_username(token):
    data = auth.decode_func(token)
    username = data['username']
    return (username)


def query(request):
    res = request.json
    print(res)

    sql = "select * \
          from seawater \
          where "
    t = list()
    for key, val in res.items():
        if (not val):
            continue
        if (key == "factor"):
            continue

        if isinstance(val, (list, tuple)):
            t.append(f"{key}>={val[0]}")
            t.append(f"{key}<={val[1]}")
        else:
            t.append(f"{key}={val}")

    sql += " and ".join(t)
    app.logger.debug(sql)

    data = db.session.execute(text(sql)).fetchall()

    return data


def draw(df_pivot: pd.DataFrame):

    import base64
    x = df_pivot.columns.values
    y = df_pivot.index.values
    z = df_pivot.values
    
    fig = plt.figure(figsize=(10, 10))
    
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    # 添加地图特征，例如海岸线、河流等

    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.RIVERS)

    # 使用pcolormesh绘制数据
    c = ax.pcolormesh(x, y, z, transform=ccrs.PlateCarree(), cmap='jet')

    # 添加一个colorbar
    fig.colorbar(c, ax=ax, orientation='vertical')

    ax.set_extent([x.min(), x.max(), y.min(), y.max()], crs=ccrs.PlateCarree())

    # 设置刻度
    xticks = df_pivot.columns.values[::8*15]
    yticks = df_pivot.index.values[::8*15]

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False,
                      linewidth=1, linestyle=':', color='k', alpha=0.8)
    gl.xlocator = mticker.FixedLocator(xticks)
    gl.ylocator = mticker.FixedLocator(yticks)

    ax.set_xticks(xticks, crs=ccrs.PlateCarree())
    ax.set_yticks(yticks, crs=ccrs.PlateCarree())

    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    # 计算温度的梯度
    gradient_y, gradient_x = np.gradient(df_pivot.to_numpy())
    # 找出梯度较大的点，这里我们假设梯度大于1的点为梯度较大的点
    large_gradient_points = np.sqrt(gradient_x**2 + gradient_y**2) > 1

    ax.contour(x, y, large_gradient_points, colors='black')


    # 将图像保存到一个BytesIO对象中，而不是一个文件
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    img_io.seek(0)

    # 将图像转换为Base64编码
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return img_base64


# 用户登录
@app.route("/api/user/login", methods=["POST"])
@cross_origin()
def user_login():
    print(request.json)
    username = request.json.get("username").strip()
    password = request.json.get("password").strip()
    sql = ('select * '
           + 'from user '
           + 'where username = "{0}" and password = "{1}"').format(username, password)
    data = db.session.execute(text(sql)).first()
    print(data)
    if data != None:
        user = dict(zip(cols, data))
        # 生成token
        token = auth.encode_func(user)
        print(token)
        return jsonify({"code": 200, "msg": "登录成功", "token": token, "role": user["role_code"]})
    else:
        return jsonify({"code": 1000, "msg": "用户名或密码错误"})

# 读取海水数据


@app.route("/api/manager/getdata", methods=["POST"])
@cross_origin()
def getdata():
    request.json["time"] = [
        f"'{(datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')+timedelta(hours=8)).date()}'" for time_str in request.json["time"]]

    data = query(request)
    count = 0
    Data = []
    for i in data:
        if (all(x is None for x in i[4:])):
            continue

        Data.append(dict(time=i[0].strftime('%Y-%m-%d'), longitude=i[1], latitude=i[2], depth=i[3],
                         temperature=i[4], salinity=i[5], density=i[6]))
        count += 1
        if (count > 20):
            break

    if (Data):
        return jsonify(status=200, msg="查询成功", data=Data, datasize=len(data))
    else:
        return jsonify(status=200, msg="查询不到相应数据", data=Data, datasize=0)

# 生成图像


@ app.route('/api/manager/generate_image', methods=["POST"])
@cross_origin()
def generate_image():
    col_name = ["time", "longitude", "latitude",
                "depth", "temperature", "salinity", "density"]
    date = (datetime.strptime(
        request.json['time'], '%Y-%m-%dT%H:%M:%S.%fZ')+timedelta(hours=8)).date()
    request.json["time"] = f"'{date}'"

    data = query(request)
    # app.logger.debug(len(data))
    if (len(data) == 0):
        return jsonify({"msg": "成功", 'image': None})
    df = pd.DataFrame(data, columns=col_name)

    img_base64 = draw(
        df.pivot(index='latitude', columns='longitude', values=request.json["factor"]))
    # 返回图像数据给前端
    app.logger.debug("success")
    return jsonify({"msg": "成功", 'image': img_base64})


@ app.route("/api/user/usermsg", methods=["POST", "GET"])
@ cross_origin()
def usermsg():
    if request.method == 'GET':
        username = get_token_username(request.headers.get('token'))
        # app.logger.debug(cols)
        res = db.session.execute(
            text('select * from user where username="%s"' % username)).fetchall()
        # app.logger.debug(f'数据: {res}')

        # Data = dict(real_name=data[0][6], sex=data[0][2], age=data[0][7], mail=data[0][4], phone=data[0][5],
        #             user_name=data[0][1], role=data[0][3])
        res = dict(zip(cols, res[0]))
        Data = dict(user_name=res["username"], role=res["role_code"])

        return jsonify(status=200, data=Data)
# 用户注册__发送验证码
# @app.route("/api/user/register/send_sms", methods=["POST"])
# @cross_origin()
# def register_sms():
#     # print(request.json)
#     phone = request.json.get("telephone")
#     # print(str(phone))
#     # params = {'code': '756821'}  # abcd就是发发送的验证码，code就是模板中定义的变量
#     # print(params)
#     # 生成随机的6位验证码
#     num = random.randrange(100000, 999999)
#     params = {'code': 123456}
#     params['code'] = num
#
#     # 将验证码保存到redis中，第一个参数是key，第二个参数是value，第三个参数表示60秒后过期
#     redis_store.set('valid_code:{}'.format(phone), num, 600)
#     print(redis_store.get('valid_code:{}'.format(phone)))
#     # 调用send_sms函数来发送短信验证码
#     result = send_sms(str(phone), json.dumps(params))
#     print(result)
#     if result[3]:
#         return jsonify({"code": "200", "msg": "验证码发送成功"})
#     else:
#         return jsonify({"code": '1000', "msg": "验证码发送失败"})


# # 用户注册__检测验证码和手机是否在数据库中
# @app.route("/api/user/findback", methods=["POST"])
# @cross_origin()
# def findback():
#     rq = request.json
#     # 获取验证码和手机号
#     password = rq.get("password")
#     vercode = rq.get("vercode")
#     telephone = rq.get("telephone")
#
#     if vercode != redis_store.get('valid_code:{}'.format(telephone)):
#         return jsonify({"status": "1000", "msg": "验证码错误"})


# 用户注册__检测（检测用户名是否在数据库中）
@ app.route("/api/user/register/test", methods=["POST"])
@ cross_origin()
def register_test():
    rq = request.json
    # 获取用户名和密码
    username = rq.get("username")
    password = rq.get("password")
    # vercode = rq.get("vercode")
    # telephone = rq.get("telephone")

    # 先判断验证码对错
    # if vercode != redis_store.get('valid_code:{}'.format(telephone)):
    #     return jsonify({"status": "1000", "msg": "验证码错误"})
    data = db.session.execute(
        text(f"select * from user where username='{username}'")).fetchall()
    if not data:
        db.session.execute(
            text(f"insert into user(username,password) value('{username}','{password}')"))
        db.session.commit()
        return jsonify({"status": "200", "msg": "注册成功"})
    else:
        return jsonify({"status": "1000", "msg": "该用户已存在,请更换用户名"})


# 用户界面获取店铺信息
@ app.route("/api/user/shop", methods=["GET"])
@ cross_origin()
def user_get_shop():
    data = db.session.execute(text('select * from fastfood_shop')).fetchall()

    Data = []
    for i in range(len(data)):
        dic = dict(shop_name=data[i][0], price=data[i][1], sale=data[i][2])
        Data.append(dic)
    print(Data)
    # return jsonify({"status":"200", "tabledata": Data})
    return jsonify(status=200, tabledata=Data)


# 下订单
@ app.route("/api/user/addorder", methods=["POST"])
@ cross_origin()
def user_addorder():
    rq = request.json
    # 获取各个参数
    shopname = rq.get("shop_name")
    ordermoney = rq.get("order_money")
    orderway = rq.get("order_way")
    consphone = get_token_phone(request.headers.get('token'))
    consname = rq.get("cons_name")
    consaddre = rq.get("cons_addre")
    create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # print(shop_name, order_money, order_way, cons_phone, cons_name, cons_addre)
    db.session.execute(text('insert into oorder( shop_name, order_money, order_way, cons_phone, cons_name, cons_addre,create_time) value("%s", %d, "%s", "%s", "%s", "%s","%s")' % (
        shopname, ordermoney, orderway, consphone, consname, consaddre, create_time)))
    db.session.commit()
    # db.session.execute('insert into fastfood_shop(shop_name, price, m_sale_v) values("解耦哎",10,100)')
    # db.session.commit()
    return jsonify(status=200, msg="成功下单")


def get_token_phone(token):
    data = auth.decode_func(token)
    phone = data['telephone']
    return (phone)


@ app.route("/api/user/unsend", methods=["POST", "GET", "DELETE"])
@ cross_origin()
def user_unsend():
    if request.method == 'GET':
        phone = get_token_phone(request.headers.get('token'))
        print(phone)
        data = db.session.execute(text(
            'select * from oorder where checked=0 and cons_phone="%s"' % phone)).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], shop_name=data[i][1], price=data[i][2], orderway=data[i][3],
                       cons_name=data[i][5], cons_addre=data[i][6], create_time=data[i][8])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)
    if request.method == 'POST':
        rq = request.json
        order_id = rq.get("order_id")
        cons_name = rq.get("cons_name")
        cons_addre = rq.get("cons_addre")
        print(order_id)
        db.session.execute(
            text('update oorder set cons_name="%s", cons_addre="%s" where order_id="%d"' % (cons_name, cons_addre, order_id)))
        db.session.commit()
        return jsonify(status=200, msg="修改成功")
    if request.method == 'DELETE':
        order_id = request.json.get("delete_id")
        db.session.execute(
            text('delete from oorder where order_id="%d" ' % order_id))
        db.session.commit()
        return jsonify(status=200, msg="删除成功")


@ app.route("/api/user/sending", methods=["POST", "GET", "DELETE"])
@ cross_origin()
def user_sending():
    if request.method == 'GET':
        phone = get_token_phone(request.headers.get('token'))

        data = db.session.execute(
            text('select * from sending_order where cons_phone="%s"' % phone)).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], shop_name=data[i][1], order_money=data[i][2], order_way=data[i][3],
                       cons_phone=data[i][4],
                       cons_name=data[i][5], cons_addre=data[i][6], disp_id=data[i][7], deliver_time=data[i][8],
                       disp_phone=data[i][9])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)


@ app.route("/api/user/sended", methods=["POST", "GET", "DELETE"])
@ cross_origin()
def user_sended():
    if request.method == 'GET':
        phone = get_token_phone(request.headers.get('token'))
        data = db.session.execute(
            text('select * from sended_order where cons_phone="%s"' % phone)).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], shop_name=data[i][1], order_money=data[i][2], order_way=data[i][3],
                       cons_phone=data[i][4],
                       cons_name=data[i][5], cons_addre=data[i][6], disp_id=data[i][7], deliver_time=data[i][8],
                       disp_phone=data[i][9])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)


@ app.route("/api/user/pwd_chg", methods=["POST"])
@ cross_origin()
def user_pwd_chg():
    if request.method == 'POST':
        pwd = request.json.get('new_pwd')
        old_pwd = request.json.get('old_pwd')
        username = get_token_username(request.headers.get('token'))
        res = db.session.execute(
            text('select * from user where username="%s" and password="%s"' %
                 (username, old_pwd))).fetchall()

        if not res:
            return jsonify(status=1000, msg="原始密码错误")
        else:
            db.session.execute(
                text('update user set password="%s" where username="%s"' % (pwd, username)))
            db.session.commit()
            return jsonify(status=200, msg="修改成功")


@ app.route("/api/manager/shop", methods=["POST", "GET", "DELETE"])
@ cross_origin()
def manager_shop():
    # 获取店铺信息
    if request.method == 'GET':
        data = db.session.execute(
            text('select * from fastfood_shop')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(shop_name=data[i][0], price=data[i][1], sale=data[i][2])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)
    if request.method == 'POST' and request.json.get('action') == "add":
        rq = request.json
        shop_name = rq.get('shop_name')
        price = rq.get('price')
        m_sale_v = rq.get('m_sale_v')
        exist = db.session.execute(
            text('select * from fastfood_shop where shop_name="%s"' % shop_name)).fetchall()
        if not exist:
            db.session.execute(text('insert fastfood_shop(shop_name,price,m_sale_v) value("%s",%d,%d)' % (
                shop_name, int(price), int(m_sale_v))))
            db.session.commit()
            return jsonify(status=200, msg="添加成功")
        else:
            return jsonify(status=1000, msg="该店铺已存在")

    if request.method == 'POST' and request.json.get('action') == "change":
        rq = request.json
        shop_name = rq.get('shop_name')
        price = rq.get('price')
        m_sale_v = rq.get('m_sale_v')
        db.session.execute(text('update fastfood_shop set price="%d", m_sale_v="%d" where shop_name="%s" ' % (
            int(price), int(m_sale_v), shop_name)))
        db.session.commit()
        return jsonify(status=200, msg="修改成功")
    if request.method == 'DELETE':
        want_delete = request.json.get('want_delete')
        db.session.execute(
            text('delete from fastfood_shop where shop_name="%s"' % want_delete))
        db.session.commit()
        return jsonify(status=200, msg="删除成功")


@ app.route("/api/manager/server", methods=["POST", "GET", "DELETE"])
@ cross_origin()
def manager_server():
    if request.method == 'GET':
        data = db.session.execute(text('select * from server')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(
                service_id=data[i][0], service_name=data[i][1], fastfood_shop_name=data[i][2])
            Data.append(dic)
        shop_range = db.session.execute(
            text('select shop_name from fastfood_shop')).fetchall()
        Shop = []
        for i in range(len(shop_range)):
            dic = dict(shop_name=shop_range[i][0])
            Shop.append(dic)
        print(Shop)
        return jsonify(status=200, tabledata=Data, shop_range=Shop)
    if request.method == 'POST':
        rq = request.json
        service_id = rq.get('service_id')
        service_name = rq.get('service_name')
        fastfood_shop_name = rq.get('fastfood_shop_name')
        exist = db.session.execute(
            text('select * from server where service_id="%s"' % service_id)).fetchall()
        if not exist:
            db.session.execute(text('insert server(service_id,service_name,fastfood_shop_name) value("%s","%s","%s")' % (
                service_id, service_name, fastfood_shop_name)))
            db.session.commit()
            return jsonify(status=200, msg="添加成功")
        else:
            return jsonify(status=1000, msg="该编号已存在")
    if request.method == 'DELETE':
        want_delete = request.json.get('want_delete')
        db.session.execute(
            text('delete from server where service_id="%s"' % want_delete))
        db.session.commit()
        return jsonify(status=200, msg="解雇成功")


@ app.route("/api/manager/dispatcher", methods=["POST", "GET", "DELETE"])
@ cross_origin()
def manager_dispatcher():
    if request.method == 'GET':
        data = db.session.execute(text('select * from dispatcher')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(
                dispatcher_id=data[i][0], dispatcher_name=data[i][1], dispatcher_phone=data[i][2])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)
    if request.method == 'POST':
        rq = request.json
        dispatcher_id = rq.get('dispatcher_id')
        dispatcher_name = rq.get('dispatcher_name')
        dispatcher_phone = rq.get('dispatcher_phone')
        exist = db.session.execute(text(
            'select * from dispatcher where dispatcher_id="%s"' % dispatcher_id)).fetchall()
        if not exist:
            db.session.execute(
                text('insert dispatcher(dispatcher_id,dispatcher_name,dispatcher_phone) value("%s","%s","%s")' % (
                    dispatcher_id, dispatcher_name, dispatcher_phone)))
            db.session.commit()
            return jsonify(status=200, msg="添加成功")
        else:
            return jsonify(status=1000, msg="该编号已存在")
    if request.method == 'DELETE':
        want_delete = request.json.get('want_delete')
        db.session.execute(
            text('delete from dispatcher where dispatcher_id="%s"' % want_delete))
        db.session.commit()
        return jsonify(status=200, msg="解雇成功")


@ app.route("/api/manager/wuliu", methods=["GET"])
@ cross_origin()
def manager_wuliu():
    ended = request.args.get('id')
    if ended == '0':
        data = db.session.execute(
            text('select * from wuliu where ended=0')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], cons_phone=data[i]
                       [1], disp_id=data[i][2], deliver_time=data[i][3])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)
    else:
        data = db.session.execute(
            text('select * from wuliu where ended=1')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], cons_phone=data[i]
                       [1], disp_id=data[i][2], deliver_time=data[i][3])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)


@ app.route("/api/manager/unsend", methods=["GET", "POST"])
@ cross_origin()
def manager_unsend():
    if request.method == 'GET':
        data = db.session.execute(
            text('select * from oorder where checked=0')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], shop_name=data[i][1], price=data[i][2], orderway=data[i][3],
                       cons_phone=data[i][4],
                       cons_name=data[i][5], cons_addre=data[i][6], create_time=data[i][8])
            Data.append(dic)

        disp_range = db.session.execute(
            text('select * from dispatcher')).fetchall()  # 获取所有的送货员就id，供选择
        Disp_range = []
        for i in range(len(disp_range)):
            dic = dict(disp_id=disp_range[i][0])
            Disp_range.append(dic)
        return jsonify(status=200, tabledata=Data, disp_range=Disp_range)
    if request.method == 'POST':
        rq = request.json
        order_id = rq.get('order_id')
        disp_id = rq.get('dispatcher_id')
        deliver_time = rq.get('deliver_time')
        cons_phone = db.session.execute(text(
            'select cons_phone from oorder where order_id="%d"' % int(order_id))).first()

        db.session.execute(text('insert wuliu( order_id, cons_phone,disp_id,deliver_time) value(%d,"%s","%s","%s")' % (
            int(order_id), cons_phone[0], disp_id, deliver_time)))
        db.session.commit()
        return jsonify(status=200, msg="成功派发")


@ app.route("/api/manager/sending", methods=["GET"])
@ cross_origin()
def manager_sending():
    if request.method == 'GET':
        data = db.session.execute(
            text('select * from sending_order')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], shop_name=data[i][1], order_money=data[i][2], order_way=data[i][3],
                       cons_phone=data[i][4],
                       cons_name=data[i][5], cons_addre=data[i][6], disp_id=data[i][7], deliver_time=data[i][8])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)


@ app.route("/api/manager/sended", methods=["GET"])
@ cross_origin()
def manager_sended():
    if request.method == 'GET':
        data = db.session.execute(
            text('select * from sended_order')).fetchall()
        Data = []
        for i in range(len(data)):
            dic = dict(order_id=data[i][0], shop_name=data[i][1], order_money=data[i][2], order_way=data[i][3],
                       cons_phone=data[i][4],
                       cons_name=data[i][5], cons_addre=data[i][6], disp_id=data[i][7], deliver_time=data[i][8])
            Data.append(dic)
        return jsonify(status=200, tabledata=Data)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port='5000')
    # 开启了debug模式
