import TaskForm from "./features/tasks/TaskForm";
import TaskList from "./features/tasks/TaskList";

function App() {
  return (
    <div>
      <h1>Redux Task Manager</h1>
      <TaskForm />
      <TaskList />
    </div>
  );
}

export default App;