import { useState} from "react"
import { useTasks } from "../context/TaskContext";



function TaskForm() {
    const [task,setTask]=useState('');

    const {addTask}= useTasks();

    const handleSubmit=(e)=>{
        e.preventDefault();
        if(task.trim()==="") return;
        addTask(task.trim());
        setTask('');
    }
    
  return (
    <div>
        <h1>TaskForm</h1>
        <form onSubmit={handleSubmit}>
        <input 
        type="text" 
        value={task}
        onChange={(e)=> setTask(e.target.value)}
        placeholder="Enter the task" />

        <button type="submit">Add Task</button>
        </form>
    </div>
  )
}

export default TaskForm