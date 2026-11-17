import { useDispatch, useSelector } from "react-redux";
import { deleteTask, toggleTask } from "./taskSlice";


function TaskList() {
  const tasks = useSelector((state) => state.tasks.items);
  const totalTask = useSelector((state) => state.tasks.totalTask);
  const dispatch=useDispatch();
  

  return (
    <div>
      <h2>Task List</h2>
    <p>Total Task : {totalTask}</p>
      {tasks.length === 0 ? (
        <p>No Task Available</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
            <h3
                style={{
                  textDecoration: task.isCompleted
                    ? "line-through"
                    : "none"
                }}
              >
                {task.title}
              </h3>
              <p>{task.description}</p>

              <p>
                Created:{" "}
                {new Date(task.createdAt).toLocaleString()}
              </p>
               <p>
                Status:{" "}
                {task.isCompleted ? "Completed" : "Pending"}
              </p>

              <button
                onClick={() => dispatch(toggleTask(task.id))}
              >
                {task.isCompleted ? "Undo" : "Complete"}
              </button>

              <button
                onClick={() => dispatch(deleteTask(task.id))}
              >
                Delete
              </button>
            </li>
            
          ))}
        </ul>
      )}
    </div>
  );
}

export default TaskList;