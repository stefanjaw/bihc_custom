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
            _logger.info(f"   DEF23 self and vals_list == 0 return\n\n")
            return super(AccountAnalyticLineCustom, self).create( vals_list )
        
        if len(vals_list) == 1:
            _logger.info(f"   DEF27 self and vals_list == 0 return\n\n")
            vals_list[0]['work_entry_id'] = False
            vals_list[0]['so_line'] = False
        _logger.info(f"   DEF30 Before Super ======= \n\n")
        analytic_line_id = super(AccountAnalyticLineCustom, self).create( vals_list )
        
        _logger.info(f"  DEF36 analytic_line_id: {analytic_line_id}\n")

        if len(analytic_line_id.task_id.sale_order_id) == 0:
            _logger.info(f"  DEF36 Antes del action_fsm_validate===\n")
            result = analytic_line_id.task_id.action_fsm_validate()
            
            _logger.info(f"  DEF38 Despues del action_fsm_validate===\n")
            analytic_line_id.order_id.order_line.timesheet_id = analytic_line_id.id
        else:
            _logger.info(f"  DEF51 analytic_line_id.task_id.sale_order_id: {analytic_line_id.task_id.sale_order_id}\n")
            so_line_id = analytic_line_id.so_line_create()
            if len(so_line_id) == 1:
                analytic_line_id.so_line = so_line_id
        
        work_entry_id = analytic_line_id.work_entry_create()
        _logger.info(f"  DEF58 work_entry_id: {work_entry_id}\n")
        analytic_line_id.work_entry_id = work_entry_id.id
        
        return analytic_line_id
    
    
    def write(self, vals):
        _logger.info(f"Updating timesheet records: {self} - {vals}\n")

        if len(self) == 0:
            _logger.info(f"    DEF58 len(self) == 0\n")
            return super(AccountAnalyticLineCustom, self).write( vals )

        vals_unit_amount = vals.get('unit_amount')
        vals_date_start = vals.get('date_start')
        vals_date_stop = vals.get('date_stop')
        _logger.info(f"    DEF65 vals_date_start: {vals_date_start} / vals_unit_amount: {vals_unit_amount} ")

        for record in self:
            _logger.info(f"    DEF66  record: {record}")
            if vals_date_start in [False, None] and vals_unit_amount not in [False, None]:
                vals['date_start'] = record.date_start
                vals['date_stop'] = record.date_start \
                                      + datetime.timedelta(hours=vals_unit_amount)
            _logger.info(f"    DEF69 vals: {vals}")
            result = super(AccountAnalyticLineCustom, record).write( vals )
            _logger.info(f"    DEF70 result: {result}\n\n")
    
            if len(record.work_entry_id) == 1:
                _logger.info(f"    DEF73 Updating record.work_entry_id: {record.work_entry_id}\n\n")
                record.work_entry_write()
            
            if len(record.so_line) == 1:
                _logger.info(f"    DEF79 Updating record.so_line: {record.so_line}\n\n")
                _logger.info(f"    DEF78 Updating record.so_line.timesheet_id: {record.so_line.timesheet_id}\n\n")
                if len(record.so_line.timesheet_id) == 0:
                    _logger.info(f"    DEF82 len(record.so_line.timesheet_id) == 0 \n\n")
                    record.so_line.timesheet_id = record.id
                    record.so_line.timesheet_ids = [record.id]
                
                _logger.info(f"    DEF86 before record.so_line_write() \n\n")
                record.so_line_write()
                
            _logger.info(f"    DEF88 before Checking so_lines_check()\n\n")
            
            record.so_lines_check()
            #STOP73
        
        return result

    '''
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

            result = super(AccountAnalyticLineCustom, analytic_line_id).write(vals)
            _logger.info(f"    DEF70 analytic_line_updated: {result}\n")
            
            work_entry_updated = analytic_line_id.work_entry_write()

            if len(analytic_line_id.task_id.sale_order_id) > 0:
                so_line_updated = analytic_line_id.so_line_write()
        
        return True
    '''
    
    def unlink(self):
        if len(self) == 0:
            return super(AccountAnalyticLineCustom, self).unlink()
        else:
            pass
            
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
            so_line_ids.qty_delivered = 0
            
        res = super(AccountAnalyticLineCustom, self).unlink()
        return res
    
    @api.onchange('date_start','unit_amount', 'date_stop')
    def update_date_stop(self):

        self.ensure_one()
        for analytic_line in self:
            _logger.info(f"    DEF100 {self.date_start},{self.unit_amount}, {self.date_stop} ")
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
        _logger.info(f"Updating Work Entry for: {self}\n")
        
        self.ensure_one()
        
        if len( self.work_entry_id ) == 0:
            _logger.info(f"    No Work Entry defined for: {self}\n")
            return False
            work_entry_ids = self.work_entry_id.search([
                ('account_analytic_line_id', '!=', False),
                ('account_analytic_line_id', '=', self.id)
            ])
            _logger.info(f"    DEF161 work_entry_ids: {work_entry_ids}\n")
            STOP161
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
        _logger.info(f"  Sale Order Line Create for: {self}/{self.id} - {self.task_id.sale_order_id}\n")
        #_logger.info(f"    DEF186 self.task_id.sale_order_id.order_line: - {self.task_id.sale_order_id.order_line}\n")
        _logger.info(f"    DEF187 Sale Order Line task_id: {self.task_id}\n")
        
        '''
        if len(self.task_id.sale_order_id ) == 0:
            _logger.info(f"    DEF190 ==== FSM Next")

            
            result = self.task_id.action_fsm_validate()
            
            self.task_id.sale_line_id = False
            self.task_id.sale_order_id.order_line.timesheet_id = self.id

            _logger.info(f"      DEF197 order_id: {self.task_id.sale_order_id}\n")
            _logger.info(f"      DEF198 order_line.timesheet_id: {self.task_id.sale_order_id.order_line.timesheet_id}\n")
        '''
        '''
            self.task_id.sale_order_id.order_line.timesheet_ids = [self.id]
            self.task_id.sale_order_id.order_line.write({
              'timesheet_ids': [self.id]
            })
            #.timesheet_ids = [self.id]
        '''
        
        # if len(self.task_id.sale_order_id) == 0:
        #     _logger.info(f"  Warning: No SO related in task_id -  Dont Create sale order line: {self.task_id.sale_order_id.order_line}\n")
        #     return self.task_id.sale_order_id.order_line
        # else:
        #     pass
        _logger.info(f"    DEF199 ====")
        # so_line_ids = self.env['sale.order.line'].search([
        #     ('order_id', '=', self.task_id.sale_order_id.id),
        #     ('timesheet_id','!=', False),
        #     ('timesheet_id','in', [self.id]),
        # ])
        
        # if len(so_line_ids) == 0:
        _logger.info(f"    DEF207 ==== len(so_line_ids) == 0")
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
        _logger.info(f"      DEF221 creating sale_order_line\n")
        so_line_id = self.env['sale.order.line'].create(so_line_data)
        _logger.info(f"      DEF223 creatd: {so_line_id}\n")
        
        # elif len(so_line_ids) == 1:
        #     _logger.info(f"    DEF225 ====")
        #     so_line_ids.timesheet_id = so_line_ids[0].timesheet_ids
        #     so_line_id = so_line_ids
        #     pass
        # else:
        #     msg = f"Error: Multiples Registers: {so_line_ids}"
        #     raise ValidationError(msg)
        
        return so_line_id
        
    def so_line_write(self):
        _logger.info(f"  DEF235 Sale Order Line Update for: {self} - {self.id}\n")
        _logger.info(f"    DEF236 self.order_id for: {self.order_id}\n")
        _logger.info(f"    DEF237 self.order_id for: {self.so_line}\n")
        _logger.info(f"    DEF238 Si está self.task_id: {self.task_id}\n")
        _logger.info(f"    DEF239 Si está self.task_id.sale_order_id: {self.task_id.sale_order_id}\n")
        _logger.info(f"    DEF240 self.task_id.sale_order_id.so_line: {self.task_id.sale_order_id.order_line}\n")
        #_logger.info(f"    DEF241 self.task_id.sale_order_id.so_line.timesheet_id: {self.task_id.sale_order_id.order_line.timesheet_id}\n")
        
        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id', '=', self.id)
        ])
        _logger.info(f"        DEF243 so_line_ids: {so_line_ids}\n")
        
        if len(so_line_ids) == 0:
            raise ValidationError(f"Not sale order lines for: {self}")
            #_logger.info(f"    DEF246 ====")
            #so_line_id = self.so_line_create()
            result = False
        elif len(so_line_ids) == 1:
            so_line_id = so_line_ids[0]
            _logger.info(f"    DEF251 ====")
            description = self.description_generate()
            so_line_id.name = description
            so_line_id.product_uom_qty = self.unit_amount
            so_line_id.qty_delivered = self.unit_amount
            result = True
        elif len(so_line_ids) > 1:
            for record in so_line_ids:
                _logger.info(f"      DEF261 record.order_id: {record.order_id}")
            
            msg = f"Found Multiple Sales Order Lines for Timesheet: {self.id}"
            raise ValidationError(msg)
        else:
            so_line_id = False
            result = False
        
        # _logger.info(f"    DEF262 so_line_id: {so_line_id}\n")
        #STOP263
        '''
        sale_order_id = self.task_id.sale_order_id
        _logger.info(f"    DEF 243 Si está sale_order_id: {sale_order_id}\n")
        _logger.info(f"    DEF 244 Si está sale_order_id: {sale_order_id.order_line.ids}\n")
        STOP245
        if len(self.so_line) == 1:
            _logger.info(f"    DEF245 ====")
            description = self.description_generate()
            self.so_line.name = description
            self.so_line.product_uom_qty = self.unit_amount
            result = True
        elif len(self.so_line) == 0:
            _logger.info(f"    DEF251 ====")
            so_line_id = self.so_line_create()
            result = True
        else:
            raise ValidationError("Error: Many sale order lines: {self.so_line}")
            result = False
        '''

        _logger.info(f"    DEF365 so_line_write ==== End \n")
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
        _logger.info(f"    DEF358 so_lines_check() self: {self.order_id.order_line}\n")
        for order_line in self.order_id.order_line:
            if len(order_line.timesheet_id) == 1 \
                and order_line.timesheet_id != order_line.timesheet_ids:
                _logger.info(f"     DEF362 Diff: {order_line} / {order_line.timesheet_id} vrs {order_line.timesheet_ids}")
                _logger.info(f"       DEF363 cambiando timesheet_ids:")
                order_line.timesheet_ids = [order_line.timesheet_id.id]
                _logger.info(f"       DEF364 Diff: {order_line} / {order_line.timesheet_id} vrs {order_line.timesheet_ids}")
                pass
            elif len(order_line.timesheet_id) == 1 \
                and order_line.timesheet_id == order_line.timesheet_ids:

                _logger.info(f"     DEF367 Iguales: {order_line} / {order_line.timesheet_id} vrs {order_line.timesheet_ids}")
        return

        #STOP354