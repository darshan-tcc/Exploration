import {useDispatch} from 'react-redux'
import { useState } from 'react'
import { addTask } from './taskSlice'

const TaskForm = () => {

    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const dispatch = useDispatch()

    const handleSubmit=(e)=>{
        e.preventDefault();

        if(title.trim()==="" || description.trim()==="") return;

        dispatch(addTask({
            id: crypto.randomUUID(),
            title:title,
            description:description,
            isCompleted:false,
            createdAt: new Date().toISOString(),
        }))

        setTitle("");
        setDescription("");
    }

    
  return (
    <div>
    <form onSubmit={handleSubmit}>

        <input type="text" 
        value={title}
        placeholder='Enter a text'
        onChange={(e)=>setTitle(e.target.value)}
        />
        <br />
        <br />
        <input type="text" value={description}
        placeholder='Enter the description'
        onChange={(e)=>setDescription(e.target.value)}
        />

<br /><br />
        <button type='submit'>Add Task</button>
    </form>
    </div>
  )
}


export default TaskForm;

