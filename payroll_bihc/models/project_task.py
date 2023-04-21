# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logging = _logger = logging.getLogger(__name__)

class payroll_custom(models.Model):
    _inherit = 'project.task'
    
    
#     def action_payroll_add(self):
#         for record in self:
#             _logger.info(f"DEF13 self: {self} timesheet_ids: {record.timesheet_ids}\n")
#             _logger.info(f"DEF14 self context: {self._context}\n")
#             #_logger.info(f"DEF14 self dir: {dir(self)}\n")
#             for timesheet_id in record.timesheet_ids:
#                 _logger.info(f"DEF17 name: {timesheet_id.name}")
#                 _logger.info(f"DEF18 Antes unit_amount: {timesheet_id.unit_amount} : {timesheet_id.timer_start} - {timesheet_id.timer_pause}")
#                 _logger.info(f"DEF19  employee_id: {timesheet_id.employee_id.name} work_entry_id: {timesheet_id.work_entry_id}")
#                 #_logger.info(f"DEF19 dir {dir(timesheet_id)}")
#                 _logger.info(f"DEF21 Despues unit_amount: {timesheet_id.unit_amount}: {timesheet_id.timer_start} - {timesheet_id.timer_pause}")
#                 _logger.info(f"DEF22 Despues unit_amount: {timesheet_id.unit_amount}: {timesheet_id.date_start} - {timesheet_id.date_stop}")
#                 if timesheet_id.date_start != False and timesheet_id.date_stop != False:
#                     duration_secs = (timesheet_id.date_stop  - timesheet_id.date_start).total_seconds()
#                     _logger.info(f"DEF25 duration_secs: {duration_secs}")
#                     duration_hrs = duration_secs / 3600
#                     _logger.info(f"DEF27 duration_hrs: {duration_hrs}")
#                     timesheet_id.write({
#                         'unit_amount': duration_hrs
#                     })
                    
#                     #STOP24
                    
#                 # timesheet_id.write({
#                 #     'timer_start': '2023-04-19 18:30:00',
#                 #     'timer_pause': '2023-04-19 18:55:00',
#                 # })
#                 break
#             break
        



# class payroll_bihc(models.Model):
#     _name = 'payroll_bihc.payroll_bihc'
#     _description = 'payroll_bihc.payroll_bihc'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
