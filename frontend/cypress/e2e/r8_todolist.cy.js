describe('R8: manipulating the todolist of a task', () => {
  let uid             
  let email           
  const taskTitle = 'Watch the introductory video'
  const youtubeKey = 'dQw4w9WgXcQ'   

  // Helper: create a fresh task with one initial todo for this user. 
  const createFreshTask = () => {
    const taskBody = new URLSearchParams()
    taskBody.append('title', taskTitle)
    taskBody.append('description', '(add a description here)')
    taskBody.append('userid', uid)
    taskBody.append('url', youtubeKey)
    taskBody.append('todos', 'Initial todo')

    return cy.request({
      method: 'POST',
      url: 'http://localhost:5000/tasks/create',
      body: taskBody.toString(),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  }
  // Helper: delete every task currently associated to the user so each test starts from a clean state. 
  const wipeTasks = () => {
    return cy.request({
      method: 'GET',
      url: `http://localhost:5000/tasks/ofuser/${uid}`,
      failOnStatusCode: false
    }).then((res) => {
      if (res.status !== 200 || !Array.isArray(res.body)) {
        return
      }
      res.body.forEach((t) => {
        cy.request({
          method: 'DELETE',
          url: `http://localhost:5000/tasks/byid/${t._id.$oid}`
        })
      })
    })
  }

  // create the test user once for the whole suite for reusing
  before(function () {
    cy.fixture('user.json').then((user) => {
      email = user.email
      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/users/create',
        form: true,
        body: user
      }).then((response) => {
        uid = response.body._id.$oid
      })
    })
  })

  // Per-test setup: reset the task state, log in, open the task in detail view. This satisfies the preconditions of UC1, UC2, and UC3.
  beforeEach(function () {
    wipeTasks().then(() => createFreshTask())

    cy.visit('http://localhost:3000')

    cy.contains('div', 'Email Address')
      .find('input[type=text]')
      .type(email)
    cy.get('form').submit()

    cy.contains('.title-overlay', taskTitle)
      .parents('.container-element')
      .find('a')
      .click()

    cy.get('.todo-list').should('be.visible')
  })

  // R8UC1 - create a new todo item

  // TC1.1 main success: non-empty description -> a new active item appears at the bottom of the list with that description.
  it('TC1.1 R8UC1 main: a non-empty description creates an active todo at the bottom', () => {
    const newDescription = 'Read chapter 1'

    cy.get('.todo-list > .todo-item').its('length').then((before) => {
      cy.get('.todo-list > li').last().find('input[type=text]')
        .scrollIntoView()
        .type(newDescription)
      cy.get('.todo-list > li').last().find('input[type=submit]').click()

      cy.get('.todo-list > .todo-item').should('have.length', before + 1)

      cy.get('.todo-list > .todo-item').last().find('.editable')
        .should('have.text', newDescription)
      cy.get('.todo-list > .todo-item').last().find('.checker')
        .should('have.class', 'unchecked')
    })
  })

  // TC1.2 alternative scenario 2.b: with an empty description, the Add
  //       button must remain disabled. "Remain" in the spec means the button is already disabled at this point.
  it('TC1.2 R8UC1 alt: the Add button is disabled when the description is empty', () => {
    cy.get('.todo-list > li').last().find('input[type=text]')
      .should('have.value', '')

    cy.get('.todo-list > li').last().find('input[type=submit]')
      .should('be.disabled')
  })


  // R8UC2 -- toggle an existing todo item

  // TC2.1 main success: clicking the icon in front of an active item sets it to done (struck through, checker becomes "checked").
  it('TC2.1 R8UC2 main: clicking the checker of an active item marks it done', () => {
    cy.get('.todo-list > .todo-item').first()
      .find('.checker').should('have.class', 'unchecked')

    cy.get('.todo-list > .todo-item').first().find('.checker').click()

    cy.get('.todo-list > .todo-item').first()
      .find('.checker').should('have.class', 'checked')

    cy.get('.todo-list > .todo-item').first()
      .find('.editable')
      .should('have.css', 'text-decoration')
      .and('match', /line-through/)
  })

  // TC2.2 alternative scenario 2.b: clicking the icon of a done item sets it back to active.
  it('TC2.2 R8UC2 alt: clicking the checker of a done item marks it active again', () => {
    cy.get('.todo-list > .todo-item').first().find('.checker').click()
    cy.get('.todo-list > .todo-item').first()
      .find('.checker').should('have.class', 'checked')

    cy.get('.todo-list > .todo-item').first().find('.checker').click()
    cy.get('.todo-list > .todo-item').first()
      .find('.checker').should('have.class', 'unchecked')

    cy.get('.todo-list > .todo-item').first()
      .find('.editable')
      .should('have.css', 'text-decoration')
      .and('not.match', /line-through/)
  })


  // R8UC3 -- delete an existing todo item 

  // TC3.1 main success: clicking the x removes the targeted item from the
  //       list. End Condition per the spec: "The todo item is removed from the todo list." 
  //       We check that the item disappears from the rendered list right after the x is clicked.
  it('TC3.1 R8UC3 main: clicking the x removes that todo from the list', () => {
    const target = 'Delete me'

    cy.get('.todo-list > li').last().find('input[type=text]')
      .scrollIntoView()
      .type(target)
    cy.get('.todo-list > li').last().find('input[type=submit]').click()

    cy.contains('.todo-list > .todo-item .editable', target).should('exist')

    cy.get('.todo-list > .todo-item').its('length').then((beforeCount) => {
      cy.contains('.todo-list > .todo-item', target)
        .find('.remover')
        .click()

      cy.contains('.todo-list > .todo-item .editable', target).should('not.exist')
      cy.get('.todo-list > .todo-item').should('have.length', beforeCount - 1)
    })
  })

  // Teardown: remove the user (and the cascade of tasks/todos).
  after(function () {
    if (uid) {
      cy.request({
        method: 'DELETE',
        url: `http://localhost:5000/users/${uid}`
      })
    }
  })
})