-- Control estructural SOLO LECTURA de public, para comparar FULL y copia restaurada.
-- No contiene DDL ni DML. PostgreSQL 17.
WITH controles AS (
SELECT 'tablas_public'::text AS control, COUNT(*)::bigint AS valor FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r'
UNION ALL SELECT 'fk_total', COUNT(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.contype='f'
UNION ALL SELECT 'fk_no_validadas', COUNT(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.contype='f' AND NOT c.convalidated
UNION ALL SELECT 'triggers_usuario', COUNT(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal
UNION ALL SELECT 'triggers_deshabilitados', COUNT(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal AND t.tgenabled='D'
UNION ALL SELECT 'pk', COUNT(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.contype='p'
UNION ALL SELECT 'check_constraints', COUNT(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.contype='c'
UNION ALL SELECT 'unique_constraints', COUNT(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.contype='u'
UNION ALL SELECT 'indices_public', COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('i','I')
UNION ALL SELECT 'secuencias_public', COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='S'
UNION ALL SELECT 'vistas_public', COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='v'
UNION ALL SELECT 'funciones_public', COUNT(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.prokind='f'
UNION ALL SELECT 'procedimientos_public', COUNT(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.prokind='p'
UNION ALL SELECT 'stock_sala_negativo', COUNT(*) FROM public.stock_sala WHERE cantidad<0
UNION ALL SELECT 'stock_deposito_negativo', COUNT(*) FROM public.stock_deposito WHERE cantidad<0
) SELECT control,valor FROM controles ORDER BY control;
