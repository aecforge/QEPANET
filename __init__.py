# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEpanet
                                 A QGIS plugin
 This plugin links QGIS and EPANET.
                             -------------------
        begin                : 2016-07-04
        copyright            : (C) 2016 by DICAM - UNITN
        email                : albertodeluca3@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QEpanet class from file QEpanet.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .qepanet import QEpanet
    return QEpanet(iface)
