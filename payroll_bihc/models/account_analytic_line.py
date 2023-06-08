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
    
    allday = fields.Boolean()
    start = fields.Datetime( )
    stop = fields.Datetime( )

    @api.model_create_multi
    def create(self, vals_list):
        if len(vals_list) == 0 and len(self) == 0:
            return self
            
        _logger.info(f"Creating record: {self}\n")
        
        analytic_line_id = super(AccountAnalyticLineCustom, self).create( vals_list )
        _logger.info(f"DEF30 a")
        so_line_id = analytic_line_id.so_line_create()
        _logger.info(f"DEF30 b")
        if len(so_line_id) == 1:
            analytic_line_id.so_line = so_line_id
        _logger.info(f"DEF30 c")
        return analytic_line_id

    def write(self, vals):
        _logger.info(f"Updating record: {self}\n")
        
        if len(self) == 0:
            return self
        
        vals_unit_amount = vals.get('unit_amount')
        vals_date_start = vals.get('date_start')
        vals_date_stop = vals.get('date_stop')
        
        if vals_date_start not in [False, None] and vals_date_stop not in [False, None]:
            date_format = "%Y-%m-%d %H:%M:%S"
            deltatime_obj = datetime.datetime.strptime(vals_date_stop, date_format) \
                          - datetime.datetime.strptime(vals_date_start, date_format)
            vals['unit_amount'] = deltatime_obj.seconds/3600
        else:
            deltatime_obj = False
        
        for analytic_line_id in self:
            if vals_date_start and vals_unit_amount:
                date_format = "%Y-%m-%d %H:%M:%S"
                date_new = datetime.datetime.strptime(vals_date_start, date_format) \
                         + datetime.timedelta(hours=vals_unit_amount)
                vals['date_stop'] = date_new.strftime(date_format)
            elif vals_date_start in [False, None] and vals_unit_amount not in [False, None]:
                vals['date_stop'] = analytic_line_id.date_start \
                                  + datetime.timedelta(hours=vals_unit_amount)
            _logger.info(f"DEF64 vals: {vals}\n")
            analytic_line_updated = super(AccountAnalyticLineCustom, analytic_line_id).write(vals)
            _logger.info(f"DEF64b vals: {vals} END\n")
            
            sale_order_int = analytic_line_id.task_id.action_view_so().get('res_id')
            sale_order_id = self.env['sale.order'].browse( sale_order_int )
            _logger.info(f"DEF64c vals: {vals} END\n")
            work_entry_updated = analytic_line_id.work_entry_write()
            _logger.info(f"DEF64d vals: {vals} END\n")
            so_line_updated = analytic_line_id.so_line_write()
            _logger.info(f"DEF64e vals: {vals} END\n")
        return True

    def unlink(self):
        _logger.info(f"Deleting record: {self}\n")
        work_entry_ids = self.env['hr.work.entry'].search([
            ('account_analytic_line_id', 'in', self.ids)
        ])
        if len(work_entry_ids) > 0:
            work_entry_ids.unlink()

        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id', 'in', self.ids)
        ])
        
        if len(so_line_ids) > 0:
            so_line_ids.product_uom_qty = 0
            
        res = super(AccountAnalyticLineCustom, self).unlink()
        
        return res
    
    @api.onchange('date_start','unit_amount', 'date_stop')
    def update_date_stop(self):

        self.ensure_one()
        for analytic_line in self:
            _logger.info(f"DEF100 {self.date_start},{self.unit_amount}, {self.date_stop} ")
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
        _logger.info(f"Updating Work Entry for record: {self}\n")
        self.ensure_one()
        work_entry_id = self.work_entry_id
        
        if len( work_entry_id ) == 0:
            work_entry_ids = work_entry_id.search([
                ('account_analytic_line_id', '!=', False),
                ('account_analytic_line_id', '=', self.id)
            ])

            if len(work_entry_ids) == 0:
                work_entry_id = self.work_entry_create()
            elif len(work_entry_ids) == 1:
                work_entry_id = work_entry_ids
            elif len(work_entry_ids) > 1:
                msg = f"Error: Multiple records: {work_entry_ids}"
                raise ValidationError(msg)
            else:
                msg = f"Error: No Work Entry found for: {self}"
                raise ValidationError(msg)
            
            self.work_entry_id = work_entry_id
        
        if len( work_entry_id ) == 0:
            msg = f"Error: No Work Entry found for: {self}"
            raise ValidationError(msg)
        else:
            description = str(self.employee_id.name) + ": " + str(self.name or "")
            vals_list = {
                    'employee_id': self.employee_id.id,
                    'name': description,
                    'date_start': self.date_start,
                    'date_stop': self.date_stop,
                    'account_analytic_line_id': self._origin.id
            }
            updated = work_entry_id.write( vals_list )
        return updated
        
        
    def work_entry_create(self):
        _logger.info(f"Creating Work Entry for record: {self}\n")
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
        _logger.info(f"DEF178 a: {self} - order_id: {self.order_id}")
        
        if len(self.order_id ) == 0:
            self.task_id.action_fsm_validate()
            _logger.info(f"DEF183 self: {self} order_id: {self.order_id}\n")
            #sale_order_int = self.task_id.action_view_so().get('res_id')
            #_logger.info(f"DEF185 sale_order_int: {sale_order_int}\n")
            #sale_order_id = self.env['sale.order'].browse( sale_order_int )
        
        if len(self.order_id) == 0:
            _logger.info(f"DEF188 Dont Create sale order line: {self.order_id.order_line}\n")
            so_line_id = self.order_id.order_line
            return so_line_id
        else:
            pass

        sale_order_id = self.order_id
        _logger.info(f"DEF194 self.order_id: {self.order_id}\n")
        
        sale_order_id.order_line.write({
            'timesheet_id': self.id,
            'timesheet_ids': [self.id]
        })
        
        #_logger.info(f"DEF201 self.order_id: {sale_order_id}\n")
        #_logger.info(f"DEF202 c")
        #sale_order_id = self.env['sale.order'].browse( sale_order_int )
        _logger.info(f"DEF204 d  sale_order_id: {sale_order_id}")
        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id','!=', False),
            ('timesheet_id','=', self.id),
        ])
        _logger.info(f"DEF178 e sale_order_id: {sale_order_id} - so_line_ids: {so_line_ids}")
        if len(so_line_ids) == 0:
            date1 = self.date
            description = f"New: {date1} {self.name}"
            description = self.description_generate()
            so_line_data = {
                'order_id': sale_order_id.id,
                'name': description,
                'product_id': self.project_id.timesheet_product_id.id,
                'product_uom': self.project_id.timesheet_product_id.uom_id.id,
                'product_uom_qty': self.unit_amount,
                'price_unit': self.project_id.timesheet_product_id.lst_price,
                'timesheet_id': self.id,
                'timesheet_ids': [self.id]
            }
            
            so_line_id = self.env['sale.order.line'].create(so_line_data)
        elif len(so_line_ids) == 1:
            so_line_id = so_line_ids
            pass
        else:
            msg = f"Error: Multiples Registers: {so_line_ids}"
            raise ValidationError(msg)
        _logger.info(f"DEF178 z")
        return so_line_id
        
    def so_line_write(self):
        description = self.description_generate()
        self.so_line.name = description
        self.so_line.product_uom_qty = self.unit_amount
        return True

    def description_generate(self):
        description = ""
        timezone_code = self._context.get('tz')
        if timezone_code not in [False, None]:
            date_start = self.date_start.astimezone( pytz.timezone(timezone_code))
            date_stop = self.date_stop.astimezone(  pytz.timezone(timezone_code))
            description = date_start.strftime('%a %b-%d %Y %I:%M %p') + " To: \n " + date_stop.strftime('%a %b-%d %I:%M %p')
        return description
