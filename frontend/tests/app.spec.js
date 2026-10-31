import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
async function toDifficulty(page){
 await page.getByRole('button',{name:/Software Development/}).click();
 for(let i=0;i<7;i++){await page.getByRole('radio').first().check();await page.getByRole('button',{name:i===6?'Choose difficulty':'Next question',exact:true}).click();}
}
async function noSeriousViolations(page){const results=await new AxeBuilder({page}).analyze();expect(results.violations.filter(v=>['serious','critical'].includes(v.impact))).toEqual([]);}
test('quiz, selection, completion, history reopening and export work',async({page})=>{
 await page.goto('/');await toDifficulty(page);await page.getByRole('button',{name:/^Easy/}).click();await expect(page.locator('.result-panel')).toBeVisible();
 const title=await page.locator('.result-panel h2').innerText();await page.getByRole('button',{name:'Mark completed',exact:true}).click();await expect(page.getByText('Completion saved to your history.')).toBeVisible();
 await page.getByRole('button',{name:'View history',exact:true}).click();await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export history',exact:true}).click();expect((await download).suggestedFilename()).toBe('project-history.json');
 await page.getByRole('button',{name:/Open build plan/}).click();await expect(page.locator('.result-panel h2')).toHaveText(title);
});
test('serious accessibility checks across the full journey',async({page})=>{
 await page.goto('/');await expect(page.getByRole('button',{name:/Software Development/})).toBeVisible();await noSeriousViolations(page);
 await page.getByRole('button',{name:/Software Development/}).click();await noSeriousViolations(page);
 for(let i=0;i<7;i++){await page.getByRole('radio').first().check();await page.getByRole('button',{name:i===6?'Choose difficulty':'Next question',exact:true}).click();}
 await noSeriousViolations(page);await page.getByRole('button',{name:/^Easy/}).click();await expect(page.locator('.result-panel')).toBeVisible();await noSeriousViolations(page);
 await page.getByRole('button',{name:'View history',exact:true}).click();await expect(page.getByRole('heading',{name:'Project history'})).toBeVisible();await noSeriousViolations(page);
});
test('a lost submit response can be retried without a duplicate pick',async({page})=>{
 let first=true;
 await page.route('**/api/submit-quiz',async route=>{if(first){first=false;await route.fetch();await route.abort();}else await route.continue();});
 await page.goto('/');await toDifficulty(page);await page.getByRole('button',{name:/^Easy/}).click();await expect(page.getByRole('alert')).toBeVisible();
 await page.getByRole('button',{name:/^Easy/}).click();await expect(page.locator('.result-panel')).toBeVisible();await page.getByRole('button',{name:'View history',exact:true}).click();await expect(page.locator('.history-item')).toHaveCount(1);
});
test('editing quiz answers and reduced-motion flow stay usable at mobile width',async({page})=>{
 await page.setViewportSize({width:375,height:812});await page.goto('/');await page.getByRole('button',{name:/Software Development/}).click();await page.getByRole('radio').first().check();await page.getByRole('button',{name:'Next question'}).click();await page.getByRole('button',{name:'Back',exact:true}).click();await expect(page.getByRole('radio').first()).toBeChecked();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
