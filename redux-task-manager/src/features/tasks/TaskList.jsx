import { useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";

import { fetchTasks,deleteTask,toggleTask } from "./taskSlice";

function TaskList() {
  const dispatch = useDispatch();

  const {
    items: tasks,
    status,
    error
  } = useSelector((state) => state.tasks);

  useEffect(() => {
    if (status === "idle") {
      dispatch(fetchTasks());
    }
  }, [dispatch, status]);

  if (status === "loading") {
    return <p>Loading tasks...</p>;
  }

  if (status === "failed") {
    return <p>Error: {error}</p>;
  }

  return (
    <div>
      <h2>My Tasks</h2>

      {tasks.length === 0 ? (
        <p>No tasks available</p>
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
                Status: {task.isCompleted
                  ? "Completed"
                  : "Pending"}
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