import {defineConfig} from '@playwright/test';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('..',import.meta.url));
export default defineConfig({
 testDir:'tests',timeout:30000,use:{baseURL:'http://localhost:5000',headless:true,reducedMotion:'reduce'},
 webServer:{command:'python app.py',cwd:root,url:'http://localhost:5000/api/health',reuseExistingServer:false,env:{APP_ORIGIN:'http://localhost:5000',DB_PATH:`${root}/data/e2e-${process.pid}.sqlite`,APP_ENV:'development',PROXY_TOKEN:''}},
 projects:[{name:'chromium',use:{browserName:'chromium'}}],
});
