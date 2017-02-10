import time
import logging
import traceback
import pandas as pd
import numpy as np

from collections import OrderedDict
from collections.abc import Sequence
from collections.abc import Mapping
from toolz.dicttoolz import merge

from sanic import Sanic
from sanic.config import Config
from sanic.response import text, json

from survey_stats import log
from survey_stats import error as sserr
from survey_stats import settings
from survey_stats import fetch
from survey_stats import state as st

Config.REQUEST_TIMEOUT = 50000000

app = Sanic(__name__)

dset_id = 'yrbss'


@app.route("/questions")
def fetch_questions(req):
    def get_meta(k, v):
        key = k.lower()
        res = (dict(st.meta[dset_id].qnmeta_dict[key], **v, id=k) if key in
               st.meta[dset_id].qnmeta_dict else dict(v, id=k))
        return res
    national = True
    combined = True
    svy = st.dset[dset_id].fetch_survey(combined, national, year=None)
    res = [(k, get_meta(k, v)) for k, v in svy.vars.items()]
    res = OrderedDict(res)
    return json(res)


@app.route('/stats/national')
def fetch_national_stats(req):
    """
    National API
    Returns mean, CI and unweighted count for a national survey
    segment from either the combined or individual yearly datasets.
    """
    return fetch_survey_stats(req, national=True, year=None)


@app.route('/stats/state')
def fetch_state_stats(req):
    """
    State API

    segment from either the combined or individual yearly datasets.
    """
    return fetch_survey_stats(req, national=False, year=None)


def remap_vars(cfg, coll, into=True):
    def map_if(pv, k):
        return pv[k] if k in pv else k
    pv = ({v: k for k, v in cfg['pop_vars'].items()} if
          not into else cfg['pop_vars'])
    res = None
    typ = type(coll)
    if isinstance(coll, str):
        res = coll
    elif isinstance(coll, Sequence):
        res = [map_if(pv, k) for k in coll]
    elif isinstance(coll, Mapping):
        res = {map_if(pv, k): remap_vars(cfg, v, into) for
               k, v in coll.items()}
    else:
        res = coll
    return res


async def fetch_survey_stats(req, national, year):
    (k, cfg) = st.dset['yrbss'].fetch_config(national, year)
    qn = req.args.get('q')
    vars = [] if not 'v' in req.args else req.args.get('v').split(',')
    resp = True if not 'r' in req.args else not 0 ** int(req.args.get('r'), 2)
    filt = {} if not 'f' in req.args else dict(
        map(lambda fv: (fv.split(':')[0],
                        fv.split(':')[1].split(',')),
            req.args.get('f').split(';')))
    svy = st.dset['yrbss'].surveys[k]
    meta = st.meta['yrbss']
    m_filt = remap_vars(cfg, filt, into=True)
    m_vars = remap_vars(cfg, vars, into=True)
    if not svy.subset(m_filt).sample_size > 1:
        raise EmptyFilterError('EmptyFilterError: %s' % (str(m_filt)))
    try:
        question = svy.vars[qn]['question']
        var_levels = remap_vars(
            cfg, {v: svy.vars[v] for v in m_vars}, into=False)
    except KeyError as err:
        raise sserr.SSInvalidUsage('KeyError: %s' % str(err), payload={
            'traceback': traceback.format_exc().splitlines(),
            'request': req.args,
            'state': {
                'q': qn,
                'svy_vars': svy.vars,
                'm_vars': m_vars
            }})
    try:
        logging.info("Ready to fetch!")
        loc = {'svy_id': k, 'dset_id': 'yrbss'}
        slices = [merge(loc, s)
                  for s in svy.generate_slices(qn, resp, m_vars, m_filt)]
        results = await fetch.fetch_all(slices)
        results = [remap_vars(cfg, x, into=False) for x in results]
        # results = await fetch.fetch_all([])
        precomp = meta.fetch_dash(qn, resp, vars, filt, national, year)
        precomp = pd.DataFrame(precomp).fillna(-1).to_dict(orient='records')
        return json({
            'q': qn,
            'filter': filt,
            'question': question,
            'response': resp,
            'vars': vars,
            'var_levels': var_levels,
            'results': results,
            'precomp': precomp
        })
    except KeyError as err:
        raise sserr.SSInvalidUsage('KeyError: %s' % str(err), payload={
            'traceback': traceback.format_exc().splitlines(),
            'request': req.args,
            'state': {
                'q': qn,
                'svy_vars': svy.vars,
                'm_vars': m_vars,
                'filter': filt,
                'response': resp,
                'var_levels': var_levels
            }})


async def fetch_survey_stats_linear(national, year):
    logging.info("requested uri: %s" % req.url)
    qn = req.args.get('q')
    vars = [] if not 'v' in req.args else req.args.get('v').split(',')
    resp = True if not 'r' in req.args else not 0 ** int(req.args.get('r'), 2)
    filt = {} if not 'f' in req.args else dict(
        map(lambda fv: (fv.split(':')[0],
                        fv.split(':')[1].split(',')),
            req.args.get('f').split(';')))
    logging.info(filt)
    combined = True
    if year:
        combined = False

    # update vars and filt column names according to pop_vars
    (k, cfg) = apst['yrbss'].fetch_config(combined, national, year)
    logging.info((k, cfg))
    replace_f = lambda x: cfg['pop_vars'][x] if x in cfg['pop_vars'] else x
    logging.info(vars)
    logging.info(filt)
    m_vars = list(map(replace_f, vars))
    m_filt = {replace_f(k): v for k, v in filt.items()}
    in_both = set(m_vars).intersection(m_filt)
    svy = apst['yrbss'].surveys[k]
    svy = svy.subset(m_filt)

    if not svy.sample_size > 1:
        raise EmptyFilterError('EmptyFilterError: %s' % (str(m_filt)))
    ivd = {v: k for k, v in cfg['pop_vars'].items()}

    # setup functions to reverse map keys for stats
    inverse_f = lambda x: ivd[x] if x in ivd else x
    replkeys_f = lambda d: {inverse_f(k): v for k, v in d.items()}

    try:
        question = svy.vars[qn]['question']
        var_levels = {inverse_f(v): svy.vars[v] for v in m_vars}
    except KeyError as err:
        raise sserr.SSInvalidUsage('KeyError: %s' % str(err), payload={
            'traceback': traceback.format_exc().splitlines(),
            'request': req.args.to_dict(),
            'state': {'q': qn, 'svy_vars': svy.vars, 'm_vars': m_vars
                      }})
    try:
        logging.info("Ready to fetch!")
        stats = svy.fetch_stats(qn, resp, m_vars, m_filt)
        g_time = g.request_time()
        logging.info('elapsed_time', g_time)
        stats = list(map(replkeys_f, stats))
        return json({
            'response': resp, 'vars': vars, 'var_levels': var_levels,
            'results': stats, '_elapsed_time': g_time
        })
    except KeyError as err:
        raise sserr.SSInvalidUsage('KeyError: %s' % str(err), payload={
            'traceback': traceback.format_exc().splitlines(),
            'request': req.args.to_dict(),
            'state': {'q': qn, 'svy_vars': svy.vars, 'm_vars': m_vars,
                      'filter': filt, 'response': resp, 'var_levels': var_levels
                      }})


def serve_app(host, port, workers, debug):
    app.run(host=host, port=port, workers=workers, debug=debug)

if __name__ == '__main__':
    serve_app(host='0.0.0.0', port=7778, workers=1, debug=True)
