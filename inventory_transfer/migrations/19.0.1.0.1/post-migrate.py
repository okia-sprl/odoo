import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Activate inventory_transfer_view_form")
    cr.execute(
        "SELECT res_id FROM ir_model_data WHERE module = 'inventory_transfer' AND name = 'inventory_transfer_view_form'"
    )
    result = cr.fetchone()
    if result:
        cr.execute("UPDATE ir_ui_view SET active = TRUE WHERE id = %s", (result[0],))
