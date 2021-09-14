/**
 * Compute the sum an array
 * @param n number of elements
 * @param array input array
 * @return sum
 */

#include <iostream>
#include <Python/Python.h>

#if PY_MAJOR_VERSION >= 3
#define PY3K
#endif

// module functions
static PyObject* message(PyObject *self, PyObject *args)
{
    char *fromPython, result[1024];
    if(!PyArg_ParseTuple(args, "s", &fromPython))
    {
        return NULL;
    }
    else
    {
        strcpy(result, "Hello, ");
        strcat(result, fromPython);
        return Py_BuildValue("s", result);
    }
}

// registration table
static PyMethodDef hello_methods[]={
        {"message", message, METH_VARARGS, "func doc"},
        {NULL, NULL, 0, NULL}
};


// module definition structure for python3
static struct PyModuleDef hellomodule = {
    PyModuleDef_HEAD_INIT,
    "hello",
    "mod doc",
    -1,
    hello_methods
};
// module initializer for python3
PyMODINIT_FUNC PyInit_hello()
{
    return PyModule_Create(&hellomodule);
}

//extern "C" // required when using C++ compiler
//long long mysum(int n, int* array) {
//    // return type is 64 bit integer
//    std::cout << "gotem";
//    long long res = 0;
//    for (int i = 0; i < n; ++i) {
//        res += array[i];
//    }
//    return res + 100;
//}