
import { updateTask } from './storage';

async function run() {
    const taskId = 'test-task-1';
    // Setup: ensure task exists
    const data = await Bun.file('./data/dashboard.json').json();
    data.tasks = [{ id: taskId, title: 'Original Title', notes: '', category: 'work', status: 'pending', priority: 'low', dueDate: '2026-01-01', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }];
    await Bun.write('./data/dashboard.json', JSON.stringify(data, null, 2));

    console.log('Starting concurrent updates...');
    
    // Fire two updates almost simultaneously
    const p1 = updateTask(taskId, { title: 'Update 1' });
    const p2 = updateTask(taskId, { notes: 'Update 2' });

    await Promise.all([p1, p2]);

    const finalData = await Bun.file('./data/dashboard.json').json();
    const task = finalData.tasks.find(t => t.id === taskId);
    
    console.log('Final Task State:', JSON.stringify(task));
    
    if (task.title === 'Update 1' && task.notes === 'Update 2') {
        console.log('✅ SUCCESS: Both updates preserved');
    } else {
        console.log('❌ FAILURE: Data lost. Title:', task.title, 'Notes:', task.notes);
        process.exit(1);
    }
}

run();
