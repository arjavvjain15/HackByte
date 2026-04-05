import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'
dotenv.config({ path: '/Users/arjavjain/HackByte4.0/frontend/ecosnap-frontend/.env' })
const supabase = createClient(process.env.VITE_SUPABASE_URL, process.env.VITE_SUPABASE_ANON_KEY)
console.log(process.env.VITE_SUPABASE_URL)
async function test() {
  const { data, error } = await supabase.from('profiles').select('id,display_name').limit(2)
  console.log("DATA:", data, "ERROR:", error)
}
test()
