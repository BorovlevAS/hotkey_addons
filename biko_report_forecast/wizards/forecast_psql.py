SQL_QUERY = """
with 
min_qty as (
	SELECT PRODUCT_ID,
		SUM(PRODUCT_MIN_QTY) as product_min_qty,
		MAX(QTY_MULTIPLE) as qty_multiple
	FROM STOCK_WAREHOUSE_ORDERPOINT
	WHERE ACTIVE
	GROUP BY PRODUCT_ID
),
product_data as (
	select
		pp.id,
		pp.default_code,
		pt.name as product_name,
		pt.uom_id as uom_id,
		uom_uom.name as uom_name,
		pt.categ_id
	from
		product_product as pp
	left join product_template as pt on (pt.id=pp.product_tmpl_id)
	left join uom_uom on (uom_uom.id=pt.uom_id)
	where
		pt.type = 'product'
),
prod_demands as (
	select 
		sm.company_id,
		sm.product_id,
		sum(sm.product_uom_qty) as qty_demand
	from stock_move as sm
	left join stock_location as sl on (sl.id=sm.location_dest_id)
	where 
		sm.state not in ('draft', 'cancel', 'done')
		and sl.usage<>'internal'
	group by
		sm.company_id,
		sm.product_id
),
prod_done as
(
	select 
		sml.company_id,
		sml.product_id,
		sum(sml.product_uom_qty) as qty_reserved,
		sum(sml.qty_done) as qty_done
	from stock_move_line as sml
	left join stock_location as sl on (sl.id=sml.location_dest_id)
	where 
		sml.state not in ('draft', 'cancel', 'done')
	group by
		sml.company_id,
		sml.product_id
),
quants as(
	select
		sq.company_id,
		sq.product_id,
		sum(sq.quantity) as quantity,
		sum(sq.reserved_quantity) as resered_quantity
	from stock_quant as sq
	left join stock_location as sl on sq.location_id=sl.id
	where
		sl.usage='internal'
	group by
		sq.company_id,
		sq.product_id
)
select
	prod_demands.company_id as company_id,
	pp.default_code as default_code,
	pp.categ_id as category_id,
	min_qty.product_min_qty as min_qty,
	min_qty.qty_multiple as min_qty_multiple,
	pp.uom_id as uom_id,
	prod_demands.product_id as product_id,
	(prod_demands.qty_demand) as qty_demand,
	(prod_done.qty_done) as qty_done,
	(prod_done.qty_reserved) as qty_reserved,
	(prod_demands.qty_demand - prod_done.qty_done - prod_done.qty_reserved) as qty_rest_demand,
	quants.quantity as rest_quantity,
	quants.resered_quantity as rest_reserved_quantity
from prod_demands as prod_demands
left join prod_done as prod_done on (prod_demands.company_id = prod_done.company_id and prod_demands.product_id = prod_done.product_id)
left join product_data as pp on (pp.id = prod_demands.product_id)
left join res_company on (res_company.id = prod_demands.company_id)
left join min_qty as min_qty on (min_qty.product_id = pp.id)
left join quants as quants on (quants.company_id=prod_demands.company_id and quants.product_id=prod_demands.product_id)
"""
