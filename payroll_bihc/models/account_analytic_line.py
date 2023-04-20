# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountAnalyticLineCustom(models.Model):
    _inherit = 'account.analytic.line'
    
    work_entry_id = fields.Many2one('hr.work.entry')
    date_start = fields.Datetime( )
    date_stop = fields.Datetime( )

    @api.onchange('date_start', 'date_stop')
    def update_dates(self):
        _logger.info(f"DEF17 self: {self}")
        for record in self:
            _logger.info(f"DEF19 record: {record}")
            if record.date_start != False and record.date_stop != False:
                duration_secs = (record.date_stop  - record.date_start).total_seconds()
                _logger.info(f"DEF25 duration_secs: {duration_secs}")
                duration_hrs = duration_secs / 3600
                _logger.info(f"DEF27 duration_hrs: {duration_hrs}")
                record.write({
                    'unit_amount': duration_hrs
                })
