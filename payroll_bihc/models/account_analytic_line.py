# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import datetime, pytz

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountAnalyticLineCustom(models.Model): # 1683736253
    _inherit = 'account.analytic.line'
    
    work_entry_id = fields.Many2one('hr.work.entry')
    date_start = fields.Datetime( default=0 )
    date_stop = fields.Datetime( default=0)
    
    @api.model_create_multi
    def create(self, vals_list):
        _logger.info(f"Creating timesheet record: {self} with vals: {vals_list}\n")
        
        if  len(self) == 0 and len(vals_list) == 0:
            return super(AccountAnalyticLineCustom, self).create( vals_list )
        
        if len(vals_list) == 1:
            vals_list[0]['work_entry_id'] = False
            vals_list[0]['so_line'] = False

        analytic_line_id = super(AccountAnalyticLineCustom, self).create( vals_list )
        
        if len(analytic_line_id.task_id.sale_order_id) == 0:
            _logger.info(f"  Action Create Sale Order\n")
            result = analytic_line_id.task_id.action_fsm_validate()
            analytic_line_id.order_id.order_line.timesheet_id = analytic_line_id.id
        else:
            _logger.info(f"    Adding Sale Order Line\n")
            so_line_id = analytic_line_id.so_line_create()
            if len(so_line_id) == 1:
                analytic_line_id.so_line = so_line_id
        
        work_entry_id = analytic_line_id.work_entry_create()
        analytic_line_id.work_entry_id = work_entry_id.id
        
        return analytic_line_id
    
    
    def write(self, vals):
        _logger.info(f"Updating timesheet records: {self} - {vals}\n")

        if len(self) == 0:
            return super(AccountAnalyticLineCustom, self).write( vals )

        vals_unit_amount = vals.get('unit_amount')
        vals_date_start = vals.get('date_start')
        vals_date_stop = vals.get('date_stop')

        for record in self:
            if vals_date_start in [False, None] and vals_unit_amount not in [False, None]:
                vals['date_start'] = record.date_start
                vals['date_stop'] = record.date_start \
                                      + datetime.timedelta(hours=vals_unit_amount)

            result = super(AccountAnalyticLineCustom, record).write( vals )
    
            if len(record.work_entry_id) == 1:
                _logger.info(f"    Updating work_entry_id: {record.work_entry_id}\n\n")
                record.work_entry_write()
            
            if len(record.so_line) == 1:
                _logger.info(f"    Updating so_line: {record.so_line}\n\n")
                if len(record.so_line.timesheet_id) == 0:
                    record.so_line.timesheet_id = record.id
                    record.so_line.timesheet_ids = [record.id]
                
                record.so_line_write()
                
            _logger.info(f"    so_lines_check()\n")
            record.so_lines_check()
        
        return result
    
    def unlink(self):
        if len(self) == 0:
            return super(AccountAnalyticLineCustom, self).unlink()
        else:
            pass
        
        _logger.info(f"Deleting record: {self}\n")

        _logger.info(f"    Deleting work_entry_ids\n")
        work_entry_ids = self.env['hr.work.entry'].search([
            ('account_analytic_line_id', 'in', self.ids)
        ])
        
        if len(work_entry_ids) > 0:
            work_entry_ids.unlink()

        _logger.info(f"    Set Sale Order Line to Qty zero\n")
        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id', 'in', self.ids)
        ])
        
        if len(so_line_ids) > 0:
            so_line_ids.product_uom_qty = 0
            so_line_ids.qty_delivered = 0
        
        res = super(AccountAnalyticLineCustom, self).unlink()
        return res
    
    @api.onchange('date_start','unit_amount', 'date_stop')
    def update_date_stop(self):

        self.ensure_one()
        for analytic_line in self:
            if    analytic_line.date_start in [False, None] \
              and analytic_line.date_stop in [False, None]:
                continue
            elif analytic_line._origin.unit_amount != analytic_line.unit_amount:
                analytic_line.date_stop = analytic_line.date_start \
                                        + datetime.timedelta(hours=analytic_line.unit_amount)
            elif analytic_line._origin.date_start != analytic_line.date_start:
                analytic_line.date_stop = analytic_line.date_start \
                                        + datetime.timedelta(hours=analytic_line.unit_amount)
            elif analytic_line.date_start in [False, None]  \
             and analytic_line.date_stop in [False, None] \
             and analytic_line.unit_amount == 0:
                 continue
            else:
                # Unknown State condition
                msg = f"Error Code with params:\n  Date Start: {analytic_line._origin.date_start}\n  Date Stop: {analytic_line._origin.date_stop}\n  Units: {analytic_line._origin.unit_amount}"
                raise ValidationError(msg)
        
        return
    
    def work_entry_write(self):
        _logger.info(f"  Updating Work Entry for: {self}\n")
        
        self.ensure_one()
        
        if len( self.work_entry_id ) == 0:
            _logger.info(f"    No Work Entry defined for: {self}\n")
            return False
        
        date_stop = self.date_start \
                  + datetime.timedelta(hours=self.unit_amount)
        
        if len( self.work_entry_id ) == 0:
            msg = f"Error: No Work Entry found for: {self}"
            raise ValidationError(msg)
        else:
            description = str(self.employee_id.name) + ": " + str(self.name or "")
            vals_list = {
                    'employee_id': self.employee_id.id,
                    'name': description,
                    'date_start': self.date_start,
                    'date_stop': date_stop,
                    'account_analytic_line_id': self._origin.id
            }
            updated = self.work_entry_id.write( vals_list )
        
        return updated
    
    def work_entry_create(self):
        _logger.info(f"  Creating Work Entry for record: {self}\n")
        description = str(self.employee_id.name) + ": " + str(self.name or "")
        vals_json = {
            'employee_id': self.employee_id.id,
            'name': description,
            'date_start': self.date_start,
            'date_stop': self.date_stop,
            'account_analytic_line_id': self.id
        }
        
        work_entry_id = self.env['hr.work.entry'].sudo().create(vals_json)
        return work_entry_id
    
    def so_line_create(self):
        _logger.info(f"  Sale Order Line Create for: {self}\n")
        
        date1 = self.date
        description = self.description_generate()
        
        so_line_data = {
            'order_id': self.task_id.sale_order_id.id,
            'name': description,
            'product_id': self.project_id.timesheet_product_id.id,
            'product_uom': self.project_id.timesheet_product_id.uom_id.id,
            'product_uom_qty': self.unit_amount,
            'price_unit': self.project_id.timesheet_product_id.lst_price,
            'timesheet_id': self.id,
            'timesheet_ids': [self.id]
        }
        so_line_id = self.env['sale.order.line'].create(so_line_data)
        
        return so_line_id
        
    def so_line_write(self):
        _logger.info(f"    Sale Order Line Update for: {self}\n")
        
        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id', '=', self.id)
        ])

        if len(so_line_ids) == 0:
            result = False
            raise ValidationError(f"Not sale order lines for: {self}")
        elif len(so_line_ids) == 1:
            so_line_id = so_line_ids[0]

            description = self.description_generate()
            so_line_id.name = description
            so_line_id.product_uom_qty = self.unit_amount
            so_line_id.qty_delivered = self.unit_amount
            result = True
        elif len(so_line_ids) > 1:
            msg = f"Found Multiple Sales Order Lines for Timesheet: {self.id}"
            raise ValidationError(msg)
        else:
            so_line_id = False
            result = False
        
        return result

    def description_generate(self):
        description = ""
        timezone_code = self._context.get('tz')
        if timezone_code not in [False, None]:
            date_start = self.date_start.astimezone( pytz.timezone(timezone_code))
            date_stop = self.date_stop.astimezone(  pytz.timezone(timezone_code))
            description = date_start.strftime('%a %b-%d %Y %I:%M %p') + " To: \n " + date_stop.strftime('%a %b-%d %I:%M %p')
        return description
    
    def so_lines_check(self):
        _logger.info(f"    so_lines_check() for self: {self}\n")
        for order_line in self.order_id.order_line:
            if len(order_line.timesheet_id) == 1 \
                and order_line.timesheet_id != order_line.timesheet_ids:
                
                order_line.timesheet_ids = [order_line.timesheet_id.id]
                pass
            elif len(order_line.timesheet_id) == 1 \
                and order_line.timesheet_id == order_line.timesheet_ids:
                pass
                
        return
