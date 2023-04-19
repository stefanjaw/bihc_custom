# -*- coding: utf-8 -*-
# from odoo import http


# class PayrollBihc(http.Controller):
#     @http.route('/payroll_bihc/payroll_bihc', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payroll_bihc/payroll_bihc/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('payroll_bihc.listing', {
#             'root': '/payroll_bihc/payroll_bihc',
#             'objects': http.request.env['payroll_bihc.payroll_bihc'].search([]),
#         })

#     @http.route('/payroll_bihc/payroll_bihc/objects/<model("payroll_bihc.payroll_bihc"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payroll_bihc.object', {
#             'object': obj
#         })
