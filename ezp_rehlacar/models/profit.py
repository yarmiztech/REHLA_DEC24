# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from datetime import date
import time
import fcntl
import socket
import struct
import macpath
from uuid import getnode as get_mac
from odoo.exceptions import UserError, ValidationError


class CarProfits(models.Model):
    _name = 'car.profit.Ref'
    _order = 'id desc'

    rehla_id = fields.Integer('Rehla Id')
    trip_id = fields.Integer('Trip Id')
    passenger_id = fields.Integer('Passenger Id')
    reh_driver_id = fields.Integer('Driver Id')
    trip_cost = fields.Float('TripCost')
    tax_amount = fields.Float('Tax Amount')
    driver_cost = fields.Float('Driver Cost')
    profit = fields.Float('Profit')
    date = fields.Date('Date')




