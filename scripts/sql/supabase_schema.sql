-- ==============================================================================
-- 🏛️ OMNICROP AI - ESQUEMA DO BANCO DE DADOS (SUPABASE POSTGRESQL + POSTGIS)
-- ARQUITETURA MULTI-TENANT ROBUSTA COM ROW LEVEL SECURITY (RLS) E GEOMETRIA
-- ==============================================================================

-- Habilita a extensão geoespacial PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. TABELA PRINCIPAL: FAZENDAS (Multi-Tenant com Row Level Security & PostGIS)
CREATE TABLE IF NOT EXISTS public.fazendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    farm_name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    geom GEOMETRY(Polygon, 4326),
    boundary_geojson JSONB,
    variedade VARCHAR(100) DEFAULT 'RB867515',
    area_ha FLOAT DEFAULT 100.0,
    alert_amarelo FLOAT DEFAULT 0.60,
    alert_vermelho FLOAT DEFAULT 0.40,
    chuva_critica FLOAT DEFAULT 30.0,
    gda_critico FLOAT DEFAULT 150.0,
    tipo_cultura VARCHAR(100) DEFAULT 'Cana-de-Açúcar',
    crop_id VARCHAR(50) DEFAULT 'sugarcane',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Migração idempotente para ambientes já existentes:
ALTER TABLE public.fazendas ADD COLUMN IF NOT EXISTS crop_id VARCHAR(50) DEFAULT 'sugarcane';

-- Habilita Row Level Security na tabela fazendas
ALTER TABLE public.fazendas ENABLE ROW LEVEL SECURITY;

-- Remove políticas anteriores caso existam
DROP POLICY IF EXISTS "Usuários acessam apenas suas próprias fazendas" ON public.fazendas;
DROP POLICY IF EXISTS "Service role tem acesso total a fazendas" ON public.fazendas;

-- Política RLS Estrita para fazendas:
-- Garante que um usuário autenticado só possa consultar, inserir, atualizar e excluir fazendas de seu próprio user_id
CREATE POLICY "Usuários acessam apenas suas próprias fazendas"
ON public.fazendas
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Política para service_role (operações administrativas/background)
CREATE POLICY "Service role tem acesso total a fazendas"
ON public.fazendas
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);


-- 2. TABELA DE CACHE: KPIS_GOLD (Medallion Data Lake -> Supabase Postgres)
-- Guarda os resumos executivos mastigados pelo pipeline da nuvem para acesso ultrarrápido
CREATE TABLE IF NOT EXISTS public.kpis_gold (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES public.fazendas(id) ON DELETE CASCADE,
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    dias_monitorados INT NOT NULL,
    chuva_total_mm FLOAT NOT NULL,
    et0_total_mm FLOAT NOT NULL,
    balanco_hidrico_mm FLOAT NOT NULL,
    dias_sem_chuva INT NOT NULL,
    gda_total_acumulado FLOAT NOT NULL,
    temp_max_media_c FLOAT NOT NULL,
    temp_min_media_c FLOAT NOT NULL,
    amplitude_termica_media_c FLOAT NOT NULL,
    risco_estresse_hidrico VARCHAR(50) NOT NULL,
    recomendacao_manejo TEXT NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT now()
);

-- Habilita Row Level Security na tabela kpis_gold
ALTER TABLE public.kpis_gold ENABLE ROW LEVEL SECURITY;

-- Remove políticas permissivas antigas
DROP POLICY IF EXISTS "Leitura autenticada de KPIs Gold" ON public.kpis_gold;
DROP POLICY IF EXISTS "Inserção permitida para serviço ou autenticado" ON public.kpis_gold;
DROP POLICY IF EXISTS "Usuários acessam apenas KPIs de suas próprias fazendas" ON public.kpis_gold;
DROP POLICY IF EXISTS "Service role tem acesso total a kpis_gold" ON public.kpis_gold;

-- POLÍTICA RLS MULTI-TENANT ESTRITA PARA KPIS_GOLD:
-- A Fazenda A NUNCA verá dados da Fazenda B.
-- O usuário autenticado só pode consultar, inserir ou modificar KPIs das fazendas cujo user_id corresponda ao seu auth.uid().
CREATE POLICY "Usuários acessam apenas KPIs de suas próprias fazendas"
ON public.kpis_gold
FOR ALL
TO authenticated
USING (
    farm_id IN (
        SELECT f.id FROM public.fazendas f WHERE f.user_id = auth.uid()
    )
)
WITH CHECK (
    farm_id IN (
        SELECT f.id FROM public.fazendas f WHERE f.user_id = auth.uid()
    )
);

-- Política para service_role (pipelines de ingestão automatizados via Azure / scripts batch)
CREATE POLICY "Service role tem acesso total a kpis_gold"
ON public.kpis_gold
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Índices de Performance, Espaciais (PostGIS GIST) e Isolamento Multi-Tenant
CREATE INDEX IF NOT EXISTS idx_fazendas_user_id ON public.fazendas(user_id);
CREATE INDEX IF NOT EXISTS idx_fazendas_geom ON public.fazendas USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_kpis_gold_farm_id ON public.kpis_gold(farm_id);
CREATE INDEX IF NOT EXISTS idx_kpis_gold_processed_at ON public.kpis_gold(processed_at DESC);
