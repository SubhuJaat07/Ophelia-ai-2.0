-- ============================================
-- Discord AI Bot - Supabase Database Schema
-- Run this in your Supabase SQL Editor
-- ============================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. GUILD_SETTINGS TABLE
-- Stores per-server configuration
-- ============================================
CREATE TABLE IF NOT EXISTS guild_settings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    guild_id TEXT UNIQUE NOT NULL,
    
    -- AI Status & Behavior
    enabled BOOLEAN DEFAULT true,
    personality TEXT DEFAULT 'fun',  -- fun, professional, casual
    
    -- Generation Parameters
    temperature REAL DEFAULT 1.02,
    max_tokens INTEGER DEFAULT 32768,
    top_p REAL DEFAULT 1.0,
    
    -- Custom Instructions (appended to system prompt)
    custom_instructions TEXT DEFAULT '',
    
    -- Reply Settings
    ping_reply_enabled BOOLEAN DEFAULT true,
    everyone_ping_reply BOOLEAN DEFAULT false,
    require_mention BOOLEAN DEFAULT true,
    reply_in_embed BOOLEAN DEFAULT false,
    
    -- AI Channels (auto-reply without mention)
    ai_channel_ids TEXT[] DEFAULT '{}',
    
    -- Feature Toggles
    memory_enabled BOOLEAN DEFAULT true,
    meta_commands_enabled BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_guild_settings_guild_id ON guild_settings(guild_id);

-- Enable Row Level Security
ALTER TABLE guild_settings ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all reads (public bot)
CREATE POLICY "Allow public read" ON guild_settings
    FOR SELECT USING (true);

-- Policy: Allow inserts (bot service role handles auth via API key)
CREATE POLICY "Allow insert" ON guild_settings
    FOR INSERT WITH CHECK (true);

-- Policy: Allow updates (bot service role handles auth via API key)
CREATE POLICY "Allow update" ON guild_settings
    FOR UPDATE USING (true);

-- ============================================
-- 2. CONVERSATIONS TABLE
-- Stores message history for context
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Guild & Channel identification
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    
    -- Message content
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Metadata
    message_id BIGINT,  -- Discord message ID if available
    tokens_used INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_conversations_guild_channel 
    ON conversations(guild_id, channel_id, created_at);

CREATE INDEX IF NOT EXISTS idx_conversations_user 
    ON conversations(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_created 
    ON conversations(created_at);

-- RLS for conversations
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON conversations
    FOR SELECT USING (true);

CREATE POLICY "Allow insert" ON conversations
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow delete" ON conversations
    FOR DELETE USING (true);

-- ============================================
-- 3. MEMORIES TABLE
-- Long-term memories about users/servers
-- ============================================
CREATE TABLE IF NOT EXISTS memories (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Guild & User identification
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'global',
    
    -- Memory content
    memory_type TEXT NOT NULL,  -- user_preference, user_info, server_fact, conversation_summary
    content TEXT NOT NULL,
    
    -- Importance scoring (higher = more important)
    REAL DEFAULT 1.0,
    
    -- Access tracking (for cache invalidation)
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_memories_guild_user 
    ON memories(guild_id, user_id, importance DESC);

CREATE INDEX IF NOT EXISTS idx_memories_type 
    ON memories(memory_type);

CREATE INDEX IF NOT EXISTS idx_memories_importance 
    ON memories(importance DESC);

-- RLS for memories
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON memories
    FOR SELECT USING (true);

CREATE POLICY "Allow insert" ON memories
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update" ON memories
    FOR UPDATE USING (true);

-- ============================================
-- 4. COMMAND_LOG TABLE (Optional)
-- Log of meta-commands executed by AI
-- ============================================
CREATE TABLE IF NOT EXISTS command_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    user_id TEXT NOT NULL,  -- Who triggered it (via AI)
    
    command_name TEXT NOT NULL,
    command_args TEXT,
    
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for command log queries
CREATE INDEX IF NOT EXISTS idx_command_log_guild 
    ON command_log(guild_id, created_at DESC);

-- RLS for command log
ALTER TABLE command_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON command_log
    FOR SELECT USING (true);

CREATE POLICY "Allow insert" ON command_log
    FOR INSERT WITH CHECK (true);

-- ============================================
-- 5. HELPER FUNCTIONS
-- ============================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for guild_settings
DROP TRIGGER IF EXISTS update_guild_settings_updated_at ON guild_settings;
CREATE TRIGGER update_guild_settings_updated_at
    BEFORE UPDATE ON guild_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean old conversations (keep last N days)
CREATE OR REPLACE FUNCTION cleanup_old_conversations(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversations 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Insert default settings example (uncomment to use)
/*
INSERT INTO guild_settings (guild_id, enabled, personality, temperature) 
VALUES ('YOUR_GUILD_ID_HERE', true, 'fun', 1.02)
ON CONFLICT (guild_id) DO NOTHING;
*/

-- ============================================
-- DONE! Your database is ready. 🎉
-- ============================================
