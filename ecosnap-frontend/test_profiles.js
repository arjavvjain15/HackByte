import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'

dotenv.config({ path: '/Users/arjavjain/HackByte4.0/backend/backend/.env' })

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY)

async function test() {
  const { data } = await supabase.from('profiles').select('*')
  console.log(data)
}
test()
