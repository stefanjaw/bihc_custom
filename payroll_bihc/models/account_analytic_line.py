# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountAnalyticLineCustom(models.Model):
    _inherit = 'account.analytic.line'
    
    work_entry_id = fields.Many2one('hr.work.entry')
    date_start = fields.Datetime( )
    date_stop = fields.Datetime( )

    @api.onchange('date_start', 'date_stop', 'name', 'employee_id', 'date', 'work_entry_id')
    def update_unit_amount(self):
        for record in self:
            _logger.info(f"  Checking Timesheets with Work Entries")
            
            if record._origin.work_entry_id.state == 'validated':
                msg = f"Can't Delete/Modify a validated work entry:\n{record._origin.work_entry_id.date_start} - {record._origin.work_entry_id.name}"
                raise ValidationError(msg)
            
            if record._origin.work_entry_id.id != False and record.work_entry_id.id == False:
                self.work_entry_archive()
            
            if record.date_start == False or record.date_stop == False:
                if record.work_entry_id.id != False:
                    record.work_entry_id.active = False
                    record.work_entry_id = False
                continue
            
            if record.date_start:
                record.date = record.date_start
                
            if record.date_start != False and record.date_stop != False:
                duration_secs = (record.date_stop  - record.date_start).total_seconds()
                duration_hrs = duration_secs / 3600

                record.unit_amount = duration_hrs
                self.work_entry_update()
            
    def work_entry_update(self):
        
        self.ensure_one()
        work_entry_id = self.work_entry_id
        
        if len( work_entry_id ) == 0:
            self.work_entry_archive()
            self.work_entry_create()

        description = str(self.employee_id.name) + ": " + str(self.name or "")
        self.work_entry_id.write({
                'employee_id': self.employee_id.id,
                'name': description,
                'date_start': self.date_start,
                'date_stop': self.date_stop,
        })
        
    def work_entry_create(self):
        description = str(self.employee_id.name) + ": " + str(self.name or "")
        
        work_entry_id = self.env['hr.work.entry'].sudo().create({
            'employee_id': self.employee_id.id,
            'name': description,
            'date_start': self.date_start,
            'date_stop': self.date_stop,
        })
        
        if len(work_entry_id) > 0:
            self.work_entry_id = work_entry_id.id
        
        return
    
    def work_entry_archive(self):
        record_ids = self.env['hr.work.entry'].sudo().search([
            ('state','!=', 'validated'),
            ('company_id','=', self.company_id.id),
            ('employee_id','=', self.employee_id.id),
            ('date_start','=', self.date_start),
            ('date_stop','=', self.date_stop),
        ])
        
        record_ids.write({
            'active': False
        })
