select table_schema, table_name from information_schema.tables
where table_schema like 'metamorpho%ethereum' or (table_schema='morpho_blue_ethereum' and table_name like '%fee%')
order by 1,2
