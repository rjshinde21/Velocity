import React from 'react'

const Card = ({icon, title, desc}) => {
  return (
    <div className='text-primary'>
        <p className=''>{title}</p>
        <p className=''>{desc}</p>
    </div>
  )
}

export default Card