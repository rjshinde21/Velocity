import { createClient } from '@supabase/supabase-js';

// Replace with your actual Supabase URL and Anon Key
const supabaseUrl = 'https://usexseafgabnwyzwjhpl.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indsa2J1ZGtkdGx0am9maGhrcnBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzIzNDM0MDAsImV4cCI6MjA0NzkxOTQwMH0.jgn_DFxRWod5G-thWQPemtAe-KLLny4Gt3zY3gRtnZ0';

const supabase = createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storage: localStorage // Ensure using localStorage
    }
});

export default supabase
