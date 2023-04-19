# -*- coding: utf-8 -*-

# from odoo import models, fields, api


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
