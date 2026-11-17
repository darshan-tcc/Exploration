
import { createContext, useContext, useMemo, useState } from "react";


const TaskContext = createContext(null);

export function TaskProvider({ children }) {

  const [tasks, setTasks] = useState([]);

  const addTask = (title) => {
    const newTask = {
        id:crypto.randomUUID(),
        title,
        completed:false
    }
    setTasks(previous => [...previous, newTask]);
  };    

  const toggleTask = (id)=>{
    setTasks(
        previous=>
            previous.map(task=> task.id ===id?{...task,completed:!task.completed}:task)

    )
  }

  const deleteTask = (index) => {
    setTasks(previous =>
      previous.filter((_, i) => i !== index)
    );
  };

  const contextValue = useMemo(
  () => ({
    tasks,
    toggleTask,
    addTask,
    deleteTask
  }),
  [tasks]
);

  return (
    <TaskContext.Provider
      value={contextValue}
    >
      {children}
    </TaskContext.Provider>
  );
}

export function useTasks(){
    const context = useContext(TaskContext);
    
    if(context==null){
        throw new Error(
            "useTasks must be used inside TaskProvider."
        );
    }

    return context;
};
