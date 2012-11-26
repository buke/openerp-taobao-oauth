# -*- coding: utf-8 -*-
##############################################################################
#    Taobao OpenERP Connector
#    Copyright 2012 wangbuke <wangbuke@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

import urllib
from osv import osv, fields
from openerp.addons.taobao.taobao_base import TaobaoMixin
import pycurl
import StringIO
import json
import logging
_logger = logging.getLogger(__name__)
import time
import openerp.tools.config as config



class taobao_shop(osv.osv, TaobaoMixin):
    _inherit = "taobao.shop"

    _columns = {
            'access_token': fields.char('access token', size=256),
            'token_type': fields.char('token type', size=256),
            'expires_in': fields.integer('expires in', help=u'实效时间，单位秒'),
            'refresh_token': fields.char('refresh_token', size=256),
            're_expires_in': fields.integer('re_expires_in', help=u'实效时间，单位秒'),
            'r1_expires_in': fields.integer('r1_expires_in', help=u'实效时间，单位秒'),
            'r2_expires_in': fields.integer('r2_expires_in', help=u'实效时间，单位秒'),
            'w1_expires_in': fields.integer('w1_expires_in', help=u'实效时间，单位秒'),
            'w2_expires_in': fields.integer('w2_expires_in', help=u'实效时间，单位秒'),

            'expires_datetime': fields.datetime(u"更新时间"),
            }

    def create(self, cr, uid, vals, context=None):
        return super(osv.osv, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        return super(osv.osv, self).write(cr, uid, ids, vals, context)

    def taobao_oauth(self, cr, uid, ids, context=None):
        shop = self._get(cr, uid, ids = ids)
        params = {}
        web_root_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        params['redirect_uri'] = web_root_url + '/taobao/%s/%d' % (cr.dbname, ids[0])
        params['client_id'] = shop.taobao_app_key
        params['response_type'] = 'code'
        url = 'https://oauth.taobao.com/authorize?%s' % urllib.urlencode(params)

        return {
            'type': 'ir.actions.act_url',
            'url':url,
            #'target': 'new'
            'target': 'self',
        }

    def taobao_get_oauth_token(self, cr, uid, ids, **kwargs):
        try:
            params = {}
            for k,v in kwargs.items():
                if v: params[k] = v

            crl = pycurl.Curl()
            crl.setopt(pycurl.CONNECTTIMEOUT, 60)
            crl.setopt(pycurl.TIMEOUT, 60)
            crl.setopt(pycurl.SSL_VERIFYPEER, 0) # need to turn off verification, because no CAs are provided
            crl.setopt(pycurl.SSL_VERIFYHOST, 0) # need to turn off verification of the host as Curl complains that the cert does not match the host
            crl.setopt(crl.POSTFIELDS,  urllib.urlencode(params))
            crl.fp = StringIO.StringIO()
            crl.setopt(pycurl.URL, 'https://oauth.taobao.com/token')
            crl.setopt(crl.WRITEFUNCTION, crl.fp.write)
            crl.perform()
            ret = json.loads(crl.fp.getvalue())

            _logger.info('%s' % (ret))

            shop = self.pool.get('taobao.shop')._save(cr, 1, ids=ids, **{
                'taobao_session_key' : str(ret['access_token']),
                'access_token' : str(ret['access_token']),
                'token_type' : str(ret['token_type']),
                'expires_in' : int(ret['expires_in']),
                'refresh_token' : str(ret['refresh_token']),
                're_expires_in' : int(ret['re_expires_in']),
                'r1_expires_in' : int(ret['r1_expires_in']),
                'r2_expires_in' : int(ret['r2_expires_in']),
                'w1_expires_in' : int(ret['w1_expires_in']),
                'w2_expires_in' : int(ret['w2_expires_in']),

                'taobao_nick' : urllib.unquote(str(ret['taobao_user_nick'])).decode('utf8'),
                'taobao_user_id' : str(ret['taobao_user_id']),
                'expires_datetime': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                'taobao_auth_type': 'bs',
                })

            for i in range(int(config.get('taobao_stream_thread_limit', 1))):
                shop_thread_name = 'taobao_app_' + shop.taobao_app_key + str(i)
                # send flag to kill threading
                from openerp.addons.taobao.taobao_top import KILL_THREAD
                KILL_THREAD[shop_thread_name] = True

            return True

        except:
            import traceback
            exc = traceback.format_exc()
            _logger.error(exc)
            return False

    def refresh_session(self, cr, uid, ids=False, context=None):
        if not ids: ids = self.search(cr, uid, [])
        if context is None: context = {}

        shops = self.browse(cr, uid, ids, context=context)
        for shop in shops:
            if shop.taobao_auth_type == 'bs':
                _logger.info('%s-%s: refresh session...' % (cr.dbname, shop.taobao_app_key))
                self.taobao_get_oauth_token(cr, uid, [shop.id],
                        client_id = shop.taobao_app_key,
                        client_secret = shop.taobao_app_secret,
                        grant_type = 'refresh_token',
                        refresh_token = shop.refresh_token,
                        )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
