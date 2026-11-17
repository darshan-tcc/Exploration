import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

const initialState = {
    items: [],
    status: "idle",
    error: null,
    totalTask: 0
}

export const fetchTasks = createAsyncThunk(
    "tasks/fetchTasks",
    async () => {
        const response = await fetch(
            "https://jsonplaceholder.typicode.com/todos?_limit=10"
        );

        if (!response.ok) {
            throw new Error("Failed to fetch tasks");
        }

        const data = await response.json();

        return data.map((task) => ({
            id: task.id,
            title: task.title,
            description: "Fetched from API",
            isCompleted: task.completed,
            createdAt: new Date().toISOString()
        }));
    }
);

const taskSlice = createSlice({
    name: 'tasks',
    initialState,
    reducers: {
        addTask: (state, action) => {
            state.items.push(action.payload);
            state.totalTask = state.items.length;
        },
        deleteTask: (state, action) => {
            state.items = state.items.filter(
                task => task.id !== action.payload
            );
            state.totalTask = state.items.length;
        },
        toggleTask: (state, action) => {
            const task = state.items.find(
                (task) => task.id === action.payload
            );

            if (task) task.isCompleted = !task.isCompleted;
        },
        extraReducers: (builder) => {
            builder
                .addCase(fetchTasks.pending, (state) => {
                    state.status = "loading";
                    state.error = null;
                })

                .addCase(fetchTasks.fulfilled, (state, action) => {
                    state.status = "succeeded";
                    state.items = action.payload;
                })

                .addCase(fetchTasks.rejected, (state, action) => {
                    state.status = "failed";
                    state.error = action.error.message;
                });
        }
    }
})

export const { addTask, deleteTask, toggleTask} = taskSlice.actions;
export default taskSlice.reducer;