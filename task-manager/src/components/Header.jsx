import { useTasks } from "../context/TaskContext";


function Header() {
  const { tasks } = useTasks();
  const completed = tasks.filter(
    tasks=>tasks.completed
  ).length;

  return (  
    <div>
        <h1>My Task Manager</h1>
        <h3>Total Tasks: {tasks.length}</h3>
        <h3>Task Complete : {completed}</h3>
        <h3>Task Pending : {tasks.length - completed}</h3>

    </div>
  );
}

export default Header;
