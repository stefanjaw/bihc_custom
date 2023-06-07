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
        
        for analytic_line_id in self:
            
            #timezone_code = self._context.get('tz')
            #if timezone_code not in [False, None]:
            #    date_start = self.date_start.astimezone( pytz.timezone(timezone_code))
            vals['date'] = analytic_line_id.date_start
            
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

    
    @api.onchange('date_start','unit_amount')
    def update_date_stop(self):
        _logger.info(f"DEF66 update_date_stop: {self} =======\n")
        self.ensure_one()
        for analytic_line in self:
            if self.date_start and self.unit_amount:
                _logger.info(f"DEF70 update_date_stop")
                analytic_line.date_stop = analytic_line.date_start + datetime.timedelta(hours=analytic_line.unit_amount)
                
                timezone_code = self._context.get('tz')
                if timezone_code not in [False, None]:
                    date_start = self.date_start.astimezone( pytz.timezone(timezone_code))
                    _logger.info(f"DEF76 update_date_stop date_start: {date_start.strftime('%d %m')}")
                    analytic_line.date = date_start
                    
                _logger.info(f"DEF79 update_date_stop date: {{analytic_line.date}} END: {analytic_line.date_stop}")
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

    # def sale_order_line_create_xxxxx(self):
    #     STOP
    #     _logger.info(f"        DEF133 sale_order_line_create: {self}\n")
    #     _logger.info(f"        DEF134 self: {self} - {self.so_line}\n=======ERROR =======\n")
        
    #     # buscar el sale order line asignado a ese timesheet_id
    #     so_line_id = self.env['sale.order.line'].search([
    #         ('timesheet_id','!=', False),
    #         ('timesheet_id','=', self.id),
    #     ])
    #     _logger.info(f"            DEF141 line_id: {so_line_id.name}\n")
    #     if len(so_line_id) > 0:
    #         # Si lo encontró no hacer nada
    #         _logger.info(f"        DEF144 Si esta ======= {self._origin.name}")
    #         pass
    #     else:
    #         _logger.info(f"           DEF147 NO esta ======= {self._origin.name}")
            
    #         # Crear un sale order line y asignarlo a este timesheet
    #         _logger.info(f"           DEF148 so_line_id: {so_line_id}")
            
    #         timezone_code = self._context.get('tz')
    #         date1 = self.date #.astimezone( pytz.timezone(timezone_code))
    #         description = f"New: {date1} {self.name}"
    #         so_line_data = {
    #             'order_id': self.task_id.sale_order_id.id,
    #             'name': description,
    #             'product_id': self.project_id.timesheet_product_id.id,
    #             'product_uom': self.project_id.timesheet_product_id.uom_id.id,
    #             'product_uom_qty': self.unit_amount,
    #             'price_unit': self.project_id.timesheet_product_id.lst_price,
    #             #'timesheet_id': self.id,
    #             #'timesheet_ids': [(6, 0, [self.id])]
    #         }
    #         _logger.info(f"DEF163 so_line_data: {so_line_data}")
            
    #         so_line_id = so_line_id.create(so_line_data)
    #         _logger.info(f"     DEF165 so_line_id: {so_line_id}\n== END ==\n")
    #         return so_line_id # xxxxxxx
    #         # {dir(so_line_id)}
    #         _logger.info(f"DEF167 timesheet_ids: {so_line_id.timesheet_ids}\n== END ==\n")
            
    #         self.so_line = so_line_id
    #         self.order_id = self.task_id.sale_order_id.id
            
    #         _logger.info(f"DEF172 timesheet_ids: {so_line_id.timesheet_ids}\n== END ==\n")

    #     return

    # @api.onchange('date_start', 'date_stop', 'name', 'employee_id', 'date', 'work_entry_id', 'unit_amount')
    # @api.onchange('date_start')
    # def update_unit_amount(self):
    #     # Utilizarlo solamente para actualizar la parte del front end
    #     # con el onchange date_start y unit_amount
    #     STOP23
    #     _logger.info(f"DEF20 update_unit_amount: {self}\n")
    #     self.ensure_one()
    #     for analytic_line in self:
    #         _logger.info(f"  Checking Timesheets with Work Entries ====\n")
            
    #         if analytic_line._origin.work_entry_id.state == 'validated':
    #             _logger.info(f"      DEF25 ====\n")
    #             msg = f"Can't Delete/Modify a validated work entry:\n{analytic_line._origin.work_entry_id.date_start} - {analytic_line._origin.work_entry_id.name}"
    #             raise ValidationError(msg)
            
    #         if analytic_line.date_start == False:
    #             _logger.info(f"      DEF30 ====\n")
    #             if analytic_line.work_entry_id.id != False:
    #                 _logger.info(f"      DEF32 ====\n")
    #                 analytic_line.work_entry_id.active = False
    #                 analytic_line.work_entry_id = False
    #             _logger.info(f"      DEF37 ====\n")
    #             #continue
            
    #         if analytic_line.date_start:
    #             _logger.info(f"      DEF41 ====\n")
    #             timezone_code = self._context.get('tz')
    #             if timezone_code not in [False, None]:
    #                 analytic_line.date = analytic_line.date_start.astimezone( pytz.timezone(timezone_code))
    #             else:
    #                 analytic_line.date = analytic_line.date_start
            
    #         if analytic_line.date_start != False and analytic_line.unit_amount != False:
    #             _logger.info(f"      DEF49 ====\n")
    #             # _logger.info(f"DEF41 analytic_line.date_start: {analytic_line.date_start}")
    #             so_line_ids = self.env['sale.order.line'].search([
    #                 ('timesheet_id', '!=', False),
    #                 ('timesheet_id', '=', analytic_line.id)
    #             ])
    #             _logger.info(f"      DEF55 ==== so_line_ids: {so_line_ids}\n")
                
    #             if len(so_line_ids) == 0:
    #                 _logger.info(f"      DEF58 ====\n")
    #                 #so_line_id = self.sale_order_line_create() # WIP XXXXXXXXXXx
    #                 #so_line_id.timesheet_id = analytic_line.id
    #                 # so_line_id.write({
    #                 #    'timesheet_id': analytic_line.id,
    #                 #    'timesheet_ids': [analytic_line.id]
    #                 # })
    #                 _logger.info(f"DEF65 self._context: {self._context}\n")
    #                 vals_list = {
    #                     'order_id': self.task_id.sale_order_id.id,
    #                     'name': f"{self._origin.id} / {self._origin.task_id.id}",  #description
    #                     'product_id': self.project_id.timesheet_product_id.id,
    #                     'product_uom': self.project_id.timesheet_product_id.uom_id.id,
    #                     'product_uom_qty': self.unit_amount,
    #                     'price_unit': self.project_id.timesheet_product_id.lst_price,
    #                     'timesheet_id': self.id,
    #                     #'timesheet_ids': [(6, 0, [self.id])]
    #                 }
    #                 so_line_id = self.env['sale.order.line'].create(vals_list)
    #                 _logger.info(f"      DEF64 ==== Created so_line_id.timesheet_id: {so_line_id.timesheet_id}\n")
    #             else:
    #                 pass
    #             # _logger.info(f"DEF43 analytic_line.date_start: {analytic_line.date_start}")
                
    #             analytic_line.date_stop = analytic_line.date_start + datetime.timedelta(hours=analytic_line.unit_amount)
    #             work_entry_id = analytic_line.work_entry_write()
    #             _logger.info(f"DEF143      work_entry_id : {work_entry_id}")
            
    #         _logger.info(f"      Updated Record: \n{analytic_line}\n{analytic_line.so_line}\n  {analytic_line.so_line.timesheet_id}")


    # def xwork_entry_missing(self):
    #     _logger.info(f"DEF259 work_entry_missing: {self}\n")
    #     _logger.info(f"DEF260 ==== Comentado el for para recorrer todos los registros ====\n=====\n")
    #     STOP170_no_deberia_estar
    #     return
    #     records = self.search([
    #         ('id', '!=', False),
    #         ('date_start', '!=', False),
    #         ('date_stop', '!=', False),
    #         ('work_entry_id','=', False)
    #     ])
    #     _logger.info(f"DEF269 records: {records}\n")
    #     for record in records:
    #         record.work_entry_write()