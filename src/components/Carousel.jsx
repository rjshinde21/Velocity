const Carousel = ({speed=20000}) => {

  const images = [
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image.jpg",
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image-1.jpg",
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image-2.jpg",
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image-3.jpg",
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image-4.jpg",
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image-5.jpg",
    "https://flowbite.s3.amazonaws.com/docs/gallery/square/image-6.jpg"
  ].map((image) => ({
    id: crypto.randomUUID(),
    image
  }));

  return (
    <>
      <div className="sm:w-[70%] w-full">
        <h1 className="bg-gradient-text pt-20 sm:pt-60 text-3xl sm:text-5xl mb-12 w-[90%] sm:w-[60%] mx-auto font-[Amenti]">
          At Velocity — We craft AI driven prompts that engage your audience
          with clarity and creativity.
        </h1>
      </div>

      {/* Backward scrolling section */}
      <div className="inner1 overflow-hidden">
        <div className="wrapper row1">
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
        </div>
      </div>

      {/* Forward scrolling section */}
      <div className="inner1 overflow-hidden">
        <div className="wrapper row2">
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
        </div>
      </div>
    </>
  );
};

export default Carousel;
