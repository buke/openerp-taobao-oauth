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
#
##############################################################################

import werkzeug.utils
import openerp
import pycurl
import StringIO
import urllib
import json
import logging
_logger = logging.getLogger(__name__)
import time

try:
    # embedded
    import openerp.addons.web.common.http as openerpweb
except ImportError:
    # standalone
    import web.common.http as openerpweb

class TaobaoOauth(openerpweb.Controller):
    _cp_path = "/taobao"

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except:
            return self.__getattribute__('index')

    @openerpweb.httprequest
    def index(self, req, *args, **kwargs):
        redirect = werkzeug.utils.redirect('/web/webclient/home')

        html_template = u"""
<html>
<body onload="timer=setTimeout(function(){ window.location='%s';}, 3000)">
<h1>%s</h1>
<p>3 秒后自动重定向到其他网页</p>
</body>
</html>
        """

        path = req.httprequest.path.split('/')
        if len(path) < 2:
            return html_template % (
                    req.httprequest.url_root,
                    '',
                    )

        if kwargs.get('error', None):
            #TODO  show error
            return html_template % (
                    req.httprequest.url_root,
                    kwargs.get('error', '') +  kwargs.get('error', 'error_description'),
                    )
        try:
            path = path[2:]
            dbname = str(path[0])
            shop_id = int(path[1])
        except:
            return html_template % (
                    req.httprequest.url_root,
                    kwargs.get('error', '') +  kwargs.get('error', 'error_description'),
                    )

        try:
            pool = openerp.pooler.get_pool(dbname)
            cr = pool.db.cursor()
            shop = pool.get('taobao.shop')._get(cr, 1, ids=[shop_id])
            pool.get('taobao.shop').taobao_get_oauth_token(cr, 1, [shop_id],
                    client_id = shop.taobao_app_key,
                    client_secret = shop.taobao_app_secret,
                    grant_type = 'authorization_code',
                    code = kwargs.get('code', None),
                    view = 'web',
                    redirect_uri = req.httprequest.url_root[:-1] + req.httprequest.path
                    )
            cr.commit()

            redirect = werkzeug.utils.redirect('/web/webclient/home#id=%d&view_type=page&model=taobao.shop' % shop_id)

        except Exception:
            raise
        finally:
            cr.close()

        return redirect


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
