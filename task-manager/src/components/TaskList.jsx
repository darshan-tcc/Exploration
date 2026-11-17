import { useTasks } from "../context/TaskContext";

function TaskList() {
  const {tasks, deleteTask, toggleTask} = useTasks();

  return (
    <div>
      <h2>My Tasks</h2>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <span
              style={{
                textDecoration: task.completed
                  ? "line-through"
                  : "none"
              }}
            >
              {task.title}
            </span>
          <button onClick={()=>toggleTask(task.id)}> {task.completed ? "Undo" : "Complete"}</button>
          <button onClick={()=>deleteTask(task.id)}>Delete</button>
          </li>
        ))}
      </ul>

    </div>
  );
}

export default TaskList;