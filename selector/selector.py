#-*- coding: utf-8 -*-

import os
import datetime

import config.config as config
import selector.util as util

import acquisition.basic as basic
import acquisition.quote_db as quote_db

import selector.plugin.hp as hp
import selector.plugin.second_wave as second_wave
import selector.plugin.tp as tp
import selector.plugin.qd as qd

import selector.plugin.z as z
import selector.plugin.d as d

import selector.plugin.zf as zf
import selector.plugin.qd as qd

import selector.selected as selected

# 横盘 第二波 突破 涨 跌 大涨 大跌
selector = {
'hp'     : hp.hp,
'hp_p'   : hp.hp_p,
'hp_pp'  : hp.hp_pp,
'hp_ppp' : hp.hp_ppp,
'2nd'    : second_wave.second_wave,
'2nd2'   : second_wave.second_wave2,
'tp'     : tp.tp,
'qd'     : qd.qd,
'z'      : z.z,
'dz'     : z.dz,
'd'      : d.d,
'dd'     : d.dd,
'zf'     : zf.zf,
'qd'     : qd.qd
}

from queue import Empty
from multiprocessing import Queue, Process

def _select(q, rq, cls):
    import util.mysqlcli as mysqlcli
    _conn = mysqlcli.get_connection()
    while True:
        try:
            #code = q.get_nowait()
            code = q.get(True, 0.1)
            #print(code)

            p = quote_db.get_price_info_df_db(code, 500, '', config.T, _conn)
            if util.filter_quote(p):
                continue

            rc = selector.get(cls)(p)
            if rc:
                selected.add_selected(code)
                rq.put(code)
        except Empty:
            #print('{0} [{1}]: finished'.format(datetime.datetime.now(), os.getpid()))
            break
        except Exception as e:
            print(e, q)
    _conn.close()

def select(cls):
    r = []
    code_list = basic.get_all_stock_code()
    #code_list = future.get_future_contract_list()

    rq = Queue()

    code_queue = Queue()
    for code in code_list:
        code_queue.put(code)

    nproc = 10
    p_list = [Process(target=_select, args=(code_queue, rq, cls,)) for i in range(nproc)]
    [p.start() for p in p_list]
    [p.join() for p in p_list]

    for _i in range(rq.qsize()):
        r.append(rq.get_nowait())

    return r
