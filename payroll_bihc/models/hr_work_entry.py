# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountAnalyticLineCustom(models.Model): # 1683737011
    _inherit = 'hr.work.entry'
    
    account_analytic_line_id = fields.Many2one('account.analytic.line')