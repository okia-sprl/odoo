def migrate_plu(cr):
    cr.execute(
        """
    SELECT pp.code, array_agg(ppl.product_id)
    FROM product_plu_line ppl
        INNER JOIN product_plu pp on ppl.plu_id = pp.id
        INNER JOIN product_product product on ppl.product_id = product.id
    WHERE product.active IS TRUE
    GROUP BY pp.code
    HAVING count(*) = 1
    ORDER BY pp.code
    """
    )

    for plu, product_tmpl_id in cr.fetchall():
        product_tmpl_id = product_tmpl_id[0]
        cr.execute("UPDATE product_product SET plu = %s WHERE id = %s", (plu, product_tmpl_id))


def migrate(cr, version):
    migrate_plu(cr)
