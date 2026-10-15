-- ==============================================================================
-- 🏛️ OMNICROP AI - ESQUEMA DO BANCO DE DADOS (SUPABASE POSTGRESQL)
-- ==============================================================================

-- 1. TABELA PRINCIPAL: FAZENDAS (Multi-Tenant com Row Level Security)
CREATE TABLE IF NOT EXISTS public.fazendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    farm_name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    variedade VARCHAR(100) DEFAULT 'RB867515',
    area_ha FLOAT DEFAULT 100.0,
    alert_amarelo FLOAT DEFAULT 0.60,
    alert_vermelho FLOAT DEFAULT 0.40,
    chuva_critica FLOAT DEFAULT 30.0,
    gda_critico FLOAT DEFAULT 150.0,
    tipo_cultura VARCHAR(100) DEFAULT 'Cana-de-Açúcar',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Habilita Row Level Security na tabela fazendas
ALTER TABLE public.fazendas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários acessam apenas suas próprias fazendas"
ON public.fazendas
FOR ALL
USING (auth.uid() = user_id);


-- 2. TABELA DE CACHE: KPIS_GOLD (Fecha o loop entre Azure Data Lake e Postgres)
-- Guarda os resumos executivos mastigados pelo pipeline da nuvem para acesso ultrarrápido
CREATE TABLE IF NOT EXISTS public.kpis_gold (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES public.fazendas(id) ON DELETE CASCADE,
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

CREATE POLICY "Leitura autenticada de KPIs Gold"
ON public.kpis_gold
FOR SELECT
USING (true);

CREATE POLICY "Inserção permitida para serviço ou autenticado"
ON public.kpis_gold
FOR INSERT
WITH CHECK (true);
