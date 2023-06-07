# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import datetime, pytz

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountAnalyticLineCustom(models.Model): # 1683736253
    _inherit = 'account.analytic.line'
    
    work_entry_id = fields.Many2one('hr.work.entry')
    date_start = fields.Datetime( )
    date_stop = fields.Datetime( )
    
    allday = fields.Boolean()
    start = fields.Datetime( )
    stop = fields.Datetime( )

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info(f"DEF20 create: {self} - vals_list: {vals_list}\n")
        if len(vals_list) == 0 and len(self) == 0:
            _logger.info(f"  DEF22 def create NO vals_list")
            return self

        analytic_line_id = super(AccountAnalyticLineCustom, self).create( vals_list )
        _logger.info(f"DEF32 create analytic_line_id: {analytic_line_id}\n")
        
        so_line_id = analytic_line_id.so_line_create()
        _logger.info(f"DEF36 create so_line_id: {so_line_id}\n")
        if len(so_line_id) == 1:
            analytic_line_id.so_line = so_line_id
        _logger.info(f"DEF38 create so_line_id: {so_line_id}\n")

        _logger.info(f"DEF40 created: {analytic_line_id}\n")
        return analytic_line_id

    def write(self, vals):
        _logger.info(f"DEF44 write: {self} - vals: {vals} =======\n")

        if len(self) == 0:
            _logger.info(f"  DEF47 def write NO vals")
            return self

        vals_unit_amount = vals.get('unit_amount')
        vals_date_start = vals.get('date_start')
        vals_date_stop = vals.get('date_stop')

        _logger.info(f"DEF52 u: {vals_unit_amount} sta: {vals_date_start} sto: {vals_date_stop} =======\n")

        # vals_fields = ["unit_amount", "date", "date_start", "date_stop"]
        # for vals_field in vals_fields:
        #     _logger.info(f"DEF56 {vals_field}")
        #     if vals.get(vals_field) not in [False, None]: vals[vals_field] = vals.get(vals_field)
        
        # STOP57
        # if vals.get('unit_amount') not in [False, None]: vals['unit_amount'] = vals.get('unit_amount')
        # if vals.get('date') not in [False, None]: vals['date'] = vals.get('date')
        # if vals.get('date_start') not in [False, None]: vals['date_start'] = vals.get('date_start')
        # if vals.get('date_stop') not in [False, None]: vals['date_stop'] = vals.get('date_stop')
        STOP64
        for analytic_line_id in self:

            
            analytic_line_updated = super(AccountAnalyticLineCustom, analytic_line_id).write(vals)
            _logger.info(f"DEF57 write analytic_line_update: {analytic_line_updated} =======\n")

            sale_order_int = analytic_line_id.task_id.action_view_so().get('res_id')
            _logger.info(f"DEF60 sale_order_int: {sale_order_int}")
            sale_order_id = self.env['sale.order'].browse( sale_order_int )
            _logger.info(f"DEF62 sale_order_id: {sale_order_id}")
            
            work_entry_updated = analytic_line_id.work_entry_write()
            _logger.info(f"DEF65 write work_entry_updated: {work_entry_updated} =======\n")
    
            so_line_updated = analytic_line_id.so_line_write()
            _logger.info(f"DEF68 write so_line_updated: {so_line_updated} =======\n")
        
        return True

    def unlink(self):
        _logger.info(f"DEF81 unlinking self: {self}")
        work_entry_ids = self.env['hr.work.entry'].search([
            ('account_analytic_line_id', 'in', self.ids)
        ])
        if len(work_entry_ids) > 0:
            _logger.info(f"DEF83 Deleting : {work_entry_ids}\n")
            work_entry_ids.unlink()

        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id', 'in', self.ids)
        ])
        if len(so_line_ids) > 0:
            _logger.info(f"DEF83 Deleting : {so_line_ids}\n")
            so_line_ids.product_uom_qty = 0
        res = super(AccountAnalyticLineCustom, self).unlink()
        return res


    
    @api.onchange('date_start','unit_amount', 'date_stop')
    def update_date_stop(self):
        _logger.info(f"DEF106 update_date_stop: {self}")
        self.ensure_one()
        for analytic_line in self:
            if analytic_line._origin.date_start != analytic_line.date_start:
                _logger.info(f"DEF110 Diferente START ====\n")
                
            if analytic_line._origin.date_stop != analytic_line.date_stop:
                _logger.info(f"DEF113 Diferente STOP ====\n")
                
            if analytic_line._origin.unit_amount != analytic_line.unit_amount:
                _logger.info(f"DEF116 Diferente Unit ====\n")

            if analytic_line._origin.date_start != analytic_line.date_start and \
               analytic_line._origin.date_stop != analytic_line.date_stop:
                    deltatime = analytic_line.date_stop - analytic_line.date_start
                    self.unit_amount = deltatime.seconds/3600
            
            if self.date_start and self.unit_amount:
                _logger.info(f"DEF126 update_date_stop bef: \n{analytic_line._origin.date_stop}  / after: \
                                {analytic_line.date_stop}=======\n")
                analytic_line.date_stop = analytic_line.date_start + datetime.timedelta(hours=analytic_line.unit_amount)
                
                timezone_code = self._context.get('tz')
                if timezone_code not in [False, None]:
                    date_start = self.date_start.astimezone( pytz.timezone(timezone_code))
                    _logger.info(f"DEF129 update_date_stop date_start: {date_start.strftime('%d %m')}")
                    analytic_line.date = date_start
                    
                _logger.info(f"DEF132 update_date_stop date: {{analytic_line.date}} END: {analytic_line.date_stop}")
        return
        

            
    
    def work_entry_write(self):
        _logger.info(f"    DEF157 work_entry_update account.analytic.line: {self}\n")
        self.ensure_one()
        work_entry_id = self.work_entry_id
        
        if len( work_entry_id ) == 0:
            _logger.info(f"      DEF162 ====\n")
            work_entry_ids = work_entry_id.search([
                ('account_analytic_line_id', '!=', False),
                ('account_analytic_line_id', '=', self.id)
            ])
            _logger.info(f"      DEF167 ==== work_entry_ids: {work_entry_ids}\n")
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
            _logger.info(f"      DEF183 Updating: {work_entry_id}====\n")
            description = str(self.employee_id.name) + ": " + str(self.name or "")
            vals_list = {
                    'employee_id': self.employee_id.id,
                    'name': description,
                    'date_start': self.date_start,
                    'date_stop': self.date_stop,
                    'account_analytic_line_id': self._origin.id
            }
            _logger.info(f"      DEF192 Updating vals_list: {vals_list}====\n")
            updated = work_entry_id.write( vals_list )
            _logger.info(f"      DEF194 Updating vals_list: {vals_list}==== {updated}\n")
        return updated
        
        
    def work_entry_create(self):
        _logger.info(f"        DEF199 work_entry_create: {self}\n")
        _logger.info(f"  Creating Work Entry")
        description = str(self.employee_id.name) + ": " + str(self.name or "")
        vals_json = {
            'employee_id': self.employee_id.id,
            'name': description,
            'date_start': self.date_start,
            'date_stop': self.date_stop,
            'account_analytic_line_id': self.id
        }
        _logger.info(f"  Creating Work Entry: {vals_json}")

        work_entry_id = self.env['hr.work.entry'].sudo().create(vals_json)
        _logger.info(f"  Creating Work Entry work_entry_id: {work_entry_id}")
        return work_entry_id
    
    def so_line_create(self):
        _logger.info(f"        DEF218 so_line_create: {self}\n")
        
        sale_order_int = self.task_id.action_view_so().get('res_id')
        _logger.info(f"    DEF246 sale_order_int: {sale_order_int}")
        
        if sale_order_int in [None, False]:
            _logger.info(f"    DEF172 Creating Sale Order\n======172======\n")
            self.task_id.action_fsm_validate()
            sale_order_int = self.task_id.action_view_so().get('res_id')
            sale_order_id = self.env['sale.order'].browse( sale_order_int )
            sale_order_id.order_line.write({
                'timesheet_id': self.id,
                'timesheet_ids': [self.id]
            })
            _logger.info(f"    DEF178b order_line.name:{sale_order_id.order_line}")
            
        _logger.info(f"DEF176 sale_order_int: {sale_order_int}")
        sale_order_id = self.env['sale.order'].browse( sale_order_int )
        _logger.info(f"DEF178a sale_order_id: {sale_order_id}")
        
        so_line_ids = self.env['sale.order.line'].search([
            ('timesheet_id','!=', False),
            ('timesheet_id','=', self.id),
        ])
        _logger.info(f"        DEF224 so_line_ids: {so_line_ids}\n")

        if len(so_line_ids) == 0:
            _logger.info(f"        DEF226 so_line_create: {self}\n")

            date1 = self.date #.astimezone( pytz.timezone(timezone_code))
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
            _logger.info(f"DEF240 so_line_data: {so_line_data}")
            
            so_line_id = self.env['sale.order.line'].create(so_line_data)
            _logger.info(f"     DEF242 so_line_id: {so_line_id}\n== END ==\n")
        elif len(so_line_ids) == 1:
            so_line_id = so_line_ids
            pass
        else:
            msg = f"Error: Multiples Registers: {so_line_ids}"
            raise ValidationError(msg)
        
        return so_line_id
        
    def so_line_write(self):
        _logger.info(f"DEF252 self: {self}===== Se Necesita ??\n")
        description = self.description_generate()
        _logger.info(f"DEF254 ===== Pendiente ===== \ndescription: {description}\n")
        self.so_line.name = description
        self.so_line.product_uom_qty = self.unit_amount
        return True

    def description_generate(self):
        _logger.info(f"DEF323 self: {self}")
        description = ""
        timezone_code = self._context.get('tz')
        if timezone_code not in [False, None]:
            date_start = self.date_start.astimezone( pytz.timezone(timezone_code))
            date_stop = self.date_stop.astimezone(  pytz.timezone(timezone_code))
            description = date_start.strftime('%a %b-%d %Y %I:%M %p') + " To: \n " + date_stop.strftime('%a %b-%d %I:%M %p')
        _logger.info(f"DEF330 description: {description} \n")
        return description
